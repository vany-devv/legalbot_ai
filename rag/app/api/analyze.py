from __future__ import annotations

import json
import logging
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.ingest import _extract_text
from app.api.schemas import AnalyzeResponse, CitationResponse
from app.core.retrieval import HybridRetriever, SearchResult
from app.dependencies import get_llm, get_retriever, get_vector_repo
from app.llm.base import LLMProvider
from app.prompts.advertising import (
    AD_ANALYSIS_SYSTEM_PROMPT,
    AD_ANALYSIS_USER_TEMPLATE,
    AD_CLASSIFY_SYSTEM_PROMPT,
    AD_CLASSIFY_USER_TEMPLATE,
)
from app.storage.pgvector import VectorRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["analyze"])

MAX_AD_TEXT_LEN = 15_000
CLASSIFY_SNIPPET_LEN = 1_000


async def _classify_ad(llm: LLMProvider, ad_text: str) -> dict:
    """Phase 1: detect ad category, target articles, checklist, and search queries."""
    snippet = ad_text[:CLASSIFY_SNIPPET_LEN]
    user_msg = AD_CLASSIFY_USER_TEMPLATE.format(ad_snippet=snippet)
    try:
        raw = await llm.complete(system=AD_CLASSIFY_SYSTEM_PROMPT, user=user_msg)
        logger.info("[CLASSIFY] LLM raw output:\n%s", raw)

        result = _parse_json(raw)

        # Validate and sanitize target_articles
        articles = result.get("target_articles", [])
        valid_articles: list[dict] = []
        for a in articles:
            if not (isinstance(a, dict) and "law" in a and "article" in a):
                continue
            law = re.sub(r"[^\d]", "", str(a["law"]))
            article = re.sub(r"[^\d.]", "", str(a["article"]))
            if law and article:
                valid_articles.append({"law": law, "article": article})

        # Always include st. 5 FZ-38 (universal advertising requirements)
        if not any(a["law"] == "38" and a["article"] == "5" for a in valid_articles):
            valid_articles.append({"law": "38", "article": "5"})

        result["target_articles"] = valid_articles

        if result.get("search_queries") or result.get("checklist"):
            logger.info(
                "[CLASSIFY] category=%r  articles=%s  checklist_items=%d",
                result.get("category"),
                valid_articles,
                len(result.get("checklist", [])),
            )
            return result

    except Exception as exc:
        logger.warning("Ad classification failed: %s", exc)

    return {
        "category": "общая реклама",
        "applicable_laws": ["38-ФЗ"],
        "target_articles": [{"law": "38", "article": "5"}, {"law": "38", "article": "28"}],
        "checklist": [
            "[ч. 3 ст. 5 ФЗ-38] Отсутствуют недостоверные или преувеличенные утверждения",
            "[ч. 7 ст. 5 ФЗ-38] Раскрыты все существенные условия",
        ],
        "search_queries": [
            ad_text[:500] + "\n\nтребования к рекламе закон о рекламе ненадлежащая реклама",
        ],
    }


async def _supplementary_search(
    retriever: HybridRetriever,
    queries: list[str],
    top_k: int = 5,
) -> list[SearchResult]:
    """Run 1-2 supplementary searches for broad coverage beyond direct lookup."""
    seen_ids: set[str] = set()
    merged: list[SearchResult] = []
    for query in queries[:2]:
        results = await retriever.search(query, top_k=top_k)
        for r in results:
            if r.chunk_id not in seen_ids:
                seen_ids.add(r.chunk_id)
                merged.append(r)
    return merged


def _normalize_extracted_text(text: str) -> str:
    """Чистит soft-wrap'ы PDF и навязывает структуру абзацев.

    Шаги:
      1) убираем мягкий перенос: <слово>-\\n<слово>  → <слово><слово>
      2) защищаем абзацные разделители (≥2 newline)
      3) одиночный \\n внутри абзаца склеиваем пробелом
      4) схлопываем повторные пробелы
      5) fallback-эвристика: если результат — один большой кусок (>500 симв),
         бьём его по предложениям, группируя ~280 симв на абзац.
    """
    if not text:
        return text
    # 1) hyphenation: «слово-\nслово» (включая «-­\n», soft-hyphen U+00AD)
    text = re.sub(r"([\wа-яА-ЯёЁ])[­-]\n([\wа-яА-ЯёЁ])", r"\1\2", text)
    # 2-4) собираем абзацы
    paragraphs = re.split(r"\n\s*\n", text)
    cleaned: list[str] = []
    for p in paragraphs:
        joined = re.sub(r"[ \t]*\n[ \t]*", " ", p)
        joined = re.sub(r"[ \t]{2,}", " ", joined).strip()
        if joined:
            cleaned.append(joined)
    result = "\n\n".join(cleaned)

    # 5) Fallback: если разделителей нет / их мало, а текст длинный — режем по предложениям.
    if len(cleaned) <= 1 and len(result) > 500:
        result = _split_by_sentences(result, target_chars=280)
    return result


def _split_by_sentences(text: str, target_chars: int = 280) -> str:
    """Режет монолитный текст на абзацы по границам предложений
    (точка/восклицание/вопрос + пробел + заглавная буква).
    Группирует ~target_chars символов в один абзац."""
    sentences = re.split(r"(?<=[.!?])\s+(?=[«\"А-ЯЁA-Z])", text)
    if len(sentences) <= 2:
        return text
    chunks: list[str] = []
    buf: list[str] = []
    cur = 0
    for s in sentences:
        buf.append(s)
        cur += len(s) + 1
        if cur >= target_chars:
            chunks.append(" ".join(buf))
            buf, cur = [], 0
    if buf:
        chunks.append(" ".join(buf))
    return "\n\n".join(chunks)


def _extract_pdf_paragraphs(content: bytes) -> str:
    """PDF-экстракция в block-режиме: PyMuPDF группирует текст по визуальным
    блокам (абзацам/заголовкам), не по строкам. Это сохраняет логику абзацев,
    тогда как `page.get_text()` без аргумента склеивает всё через \\n на каждой
    строке и теряет структуру.
    """
    import fitz

    doc = fitz.open(stream=content, filetype="pdf")
    paragraphs: list[str] = []
    for page in doc:
        for block in page.get_text("blocks"):
            # block: (x0, y0, x1, y1, text, block_no, block_type)
            if len(block) >= 7 and block[6] != 0:
                continue  # пропускаем не-текстовые блоки (изображения)
            text = (block[4] if len(block) > 4 else "") or ""
            text = text.strip()
            if text:
                paragraphs.append(text)
    return "\n\n".join(paragraphs)


async def _resolve_ad_text(
    text: str | None, file: UploadFile | None,
) -> str:
    if file is not None:
        content = await file.read()
        filename = file.filename or "upload.txt"
        if filename.lower().endswith(".pdf"):
            extracted = _extract_pdf_paragraphs(content)
        else:
            extracted = _extract_text(content, filename)
        if not extracted.strip():
            raise HTTPException(status_code=422, detail="Could not extract text from file")
        return _normalize_extracted_text(extracted)
    if text:
        return text
    raise HTTPException(status_code=422, detail="Provide either 'text' or 'file'")


def _build_structured_context(
    mandatory: list[SearchResult],
    supplementary: list[SearchResult],
) -> tuple[str, str]:
    """Build two context sections: mandatory (direct lookup) and supplementary (retrieval).

    Mandatory chunks are grouped by (law, article) and concatenated to reconstruct
    multi-chunk articles as a single continuous text block.
    Supplementary drops any (law, article) already covered by mandatory.
    """
    # Group mandatory by (law, article), preserving chunk order (already sorted by chunk_index)
    groups: dict[tuple[str, str], list[SearchResult]] = {}
    for r in mandatory:
        key = (r.meta.get("law", ""), r.meta.get("article", ""))
        groups.setdefault(key, []).append(r)

    mandatory_parts: list[str] = []
    for i, ((law, article), chunks) in enumerate(groups.items(), 1):
        header = f"[{i}] {law}" + (f", ст. {article}" if article else "")
        combined = "\n".join(c.content for c in chunks)
        mandatory_parts.append(f"{header}\n{combined}")

    mandatory_ctx = "\n\n---\n\n".join(mandatory_parts) if mandatory_parts else "(нет)"

    # Build supplementary, skipping (law, article) already in mandatory
    covered: set[tuple[str, str]] = set(groups.keys())
    supp_parts: list[str] = []
    supp_idx = len(groups) + 1
    for r in supplementary:
        key = (r.meta.get("law", ""), r.meta.get("article", ""))
        if key in covered:
            continue
        covered.add(key)
        law, article = key
        header = f"[{supp_idx}] {law}" + (f", ст. {article}" if article else "")
        supp_parts.append(f"{header}\n{r.content}")
        supp_idx += 1

    supplementary_ctx = "\n\n---\n\n".join(supp_parts) if supp_parts else "(нет)"

    return mandatory_ctx, supplementary_ctx


def _build_all_citations(
    mandatory: list[SearchResult],
    supplementary: list[SearchResult],
) -> list[CitationResponse]:
    """Build deduplicated citation list: mandatory first, one entry per (law, article)."""
    seen: set[tuple[str, str]] = set()
    result: list[CitationResponse] = []

    for r in mandatory:
        key = (r.meta.get("law", r.document_id), r.meta.get("article", ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(CitationResponse(
            chunk_id=r.chunk_id,
            document_id=r.document_id,
            content=r.content,
            retrieval_score=r.score,
            meta=r.meta,
        ))

    for r in supplementary:
        key = (r.meta.get("law", r.document_id), r.meta.get("article", ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(CitationResponse(
            chunk_id=r.chunk_id,
            document_id=r.document_id,
            content=r.content,
            retrieval_score=r.score,
            meta=r.meta,
        ))

    return result


@router.post("", response_model=AnalyzeResponse)
async def analyze(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    top_k: int = Form(default=5),
    retriever: HybridRetriever = Depends(get_retriever),
    repo: VectorRepository = Depends(get_vector_repo),
    llm: LLMProvider = Depends(get_llm),
) -> AnalyzeResponse:
    logger.info("analyze_started", extra={"top_k": top_k, "has_file": file is not None, "stream": False})
    ad_text = await _resolve_ad_text(text, file)
    if len(ad_text) > MAX_AD_TEXT_LEN:
        ad_text = ad_text[:MAX_AD_TEXT_LEN]

    classification = await _classify_ad(llm, ad_text)

    mandatory, supplementary = await _fetch_both(
        repo, retriever, classification, top_k,
    )
    mandatory_ctx, supplementary_ctx = _build_structured_context(mandatory, supplementary)

    checklist_str = _format_checklist(classification.get("checklist", []))
    user_msg = AD_ANALYSIS_USER_TEMPLATE.format(
        category=classification.get("category", "не определена"),
        applicable_laws=", ".join(classification.get("applicable_laws", ["38-ФЗ"])),
        checklist=checklist_str,
        ad_text=ad_text,
        mandatory_context=mandatory_ctx,
        supplementary_context=supplementary_ctx,
    )

    logger.info(
        "[ANALYZE] mandatory_articles=%d  supplementary_articles=%d",
        len({(r.meta.get("law"), r.meta.get("article")) for r in mandatory}),
        len({(r.meta.get("law"), r.meta.get("article")) for r in supplementary}),
    )

    raw = await llm.complete(system=AD_ANALYSIS_SYSTEM_PROMPT, user=user_msg)
    logger.info("[ANALYZE] LLM raw output:\n%s", raw)

    parsed = _parse_json(raw)
    risks = parsed.get("risks", [])
    logger.info(
        "analyze_completed",
        extra={
            "overall": parsed.get("overall_risk_level"),
            "risks_count": len(risks),
            "category": classification.get("category"),
        },
    )

    return AnalyzeResponse(
        risks=risks,
        summary=parsed.get("summary", raw),
        overall_risk_level=parsed.get("overall_risk_level", "unknown"),
        citations=_build_all_citations(mandatory, supplementary),
    )


@router.post("/stream")
async def analyze_stream(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    top_k: int = Form(default=5),
    retriever: HybridRetriever = Depends(get_retriever),
    repo: VectorRepository = Depends(get_vector_repo),
    llm: LLMProvider = Depends(get_llm),
) -> StreamingResponse:
    logger.info("analyze_started", extra={"top_k": top_k, "has_file": file is not None, "stream": True})
    ad_text = await _resolve_ad_text(text, file)
    if len(ad_text) > MAX_AD_TEXT_LEN:
        ad_text = ad_text[:MAX_AD_TEXT_LEN]

    async def generate():
        def _event(payload: dict) -> str:
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # Извлечённый текст материала — фронт использует для inline-подсветки фрагментов риска
        yield _event({"type": "ad_text", "text": ad_text})

        yield _event({"type": "thinking", "text": "Определяю категорию и применимые нормы..."})

        classification = await _classify_ad(llm, ad_text)
        category = classification.get("category", "не определена")
        yield _event({"type": "thinking", "text": f"Категория: {category}. Загружаю нормативные акты..."})

        mandatory, supplementary = await _fetch_both(repo, retriever, classification, top_k)
        total = len(set((r.meta.get("law", ""), r.meta.get("article", "")) for r in mandatory + supplementary))
        yield _event({"type": "thinking", "text": f"Загружено {total} статей. Анализирую на соответствие..."})

        mandatory_ctx, supplementary_ctx = _build_structured_context(mandatory, supplementary)
        logger.info(
            "[ANALYZE] mandatory_articles=%d  supplementary_articles=%d",
            len({(r.meta.get("law"), r.meta.get("article")) for r in mandatory}),
            len({(r.meta.get("law"), r.meta.get("article")) for r in supplementary}),
        )

        checklist_str = _format_checklist(classification.get("checklist", []))
        user_msg = AD_ANALYSIS_USER_TEMPLATE.format(
            category=category,
            applicable_laws=", ".join(classification.get("applicable_laws", ["38-ФЗ"])),
            checklist=checklist_str,
            ad_text=ad_text,
            mandatory_context=mandatory_ctx,
            supplementary_context=supplementary_ctx,
        )

        raw = await llm.complete(system=AD_ANALYSIS_SYSTEM_PROMPT, user=user_msg)
        logger.info("[ANALYZE] LLM raw output:\n%s", raw)

        parsed = _parse_json(raw)
        risks = parsed.get("risks", [])
        logger.info(
            "analyze_completed",
            extra={
                "overall": parsed.get("overall_risk_level"),
                "risks_count": len(risks),
                "category": category,
            },
        )

        yield _event({"type": "result", "data": parsed})

        citations_data = [c.model_dump() for c in _build_all_citations(mandatory, supplementary)]
        yield _event({"type": "citations", "data": citations_data})
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


async def _fetch_both(
    repo: VectorRepository,
    retriever: HybridRetriever,
    classification: dict,
    top_k: int,
) -> tuple[list[SearchResult], list[SearchResult]]:
    """Fetch mandatory (direct lookup) and supplementary (retrieval) in parallel."""
    import asyncio

    mandatory_task = asyncio.create_task(
        repo.fetch_by_articles(classification.get("target_articles", []))
    )
    supplementary_task = asyncio.create_task(
        _supplementary_search(retriever, classification.get("search_queries", []), top_k=top_k)
    )
    mandatory, supplementary = await asyncio.gather(mandatory_task, supplementary_task)
    return mandatory, supplementary


def _format_checklist(items: list[str]) -> str:
    if items:
        return "\n".join(f"- {item}" for item in items)
    return "- Общие требования ФЗ-38"


def _parse_json(raw: str) -> dict:
    """Try to parse LLM output as JSON, handling markdown code blocks."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n", 1)
        text = lines[1] if len(lines) > 1 else text
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
    return {}
