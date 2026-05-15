from __future__ import annotations

import json
import logging
import re
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.ingest import _extract_text
from app.api.schemas import AnalyzeResponse, CitationResponse
from app.config import settings
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
# Stage 1 видит начало + конец: рекламные маркеры (слово "РЕКЛАМА",
# номера лицензий, контакты, домен/призыв к действию) обычно в конце
# материала. Если брать только начало — нативная реклама с образовательной
# подачей классифицируется как informational и все нарушения теряются.
CLASSIFY_HEAD_LEN = 1_500
CLASSIFY_TAIL_LEN = 800

# Лимит размера загружаемого файла. Возвращается 413 при превышении.
# Должен соответствовать UI-подписи в frontend/pages/analyze/index.vue.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 МБ


def _build_classify_snippet(ad_text: str) -> str:
    """Готовит сниппет для Stage 1: первые N символов + последние M.

    В рекламных материалах ключевые сигналы (слово "РЕКЛАМА", лицензия,
    контакты, домен) часто находятся в конце. Просто `text[:N]` теряет их
    для длинных нативных реклам.
    """
    if len(ad_text) <= CLASSIFY_HEAD_LEN + CLASSIFY_TAIL_LEN:
        return ad_text
    head = ad_text[:CLASSIFY_HEAD_LEN]
    tail = ad_text[-CLASSIFY_TAIL_LEN:]
    return f"{head}\n\n[...середина пропущена...]\n\n{tail}"


async def _classify_ad(llm: LLMProvider, ad_text: str) -> dict:
    """Phase 1: detect ad category, target articles, checklist, and search queries."""
    snippet = _build_classify_snippet(ad_text)
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

        # Нормализуем None на безопасные дефолты — иначе .join() / .get() с дефолтом
        # будут получать None и ломаться (LLM может вернуть ключ со значением null).
        if not isinstance(result.get("applicable_laws"), list):
            result["applicable_laws"] = ["ФЗ-38"]
        if not isinstance(result.get("checklist"), list):
            result["checklist"] = []
        if not isinstance(result.get("search_queries"), list):
            result["search_queries"] = []
        if not isinstance(result.get("object_identifiers"), list):
            result["object_identifiers"] = []
        if not isinstance(result.get("material_kind"), str):
            result["material_kind"] = "informational"
        if not isinstance(result.get("found_attributes"), dict):
            result["found_attributes"] = {}

        if result.get("search_queries") or result.get("checklist"):
            logger.info(
                "[CLASSIFY] material_kind=%r category=%r articles=%s checklist_items=%d",
                result.get("material_kind"),
                result.get("category"),
                valid_articles,
                len(result.get("checklist", [])),
            )
            return result

    except Exception as exc:
        logger.warning("Ad classification failed: %s", exc)

    # Fallback: безопасный набор, проверяющий только формулировки по ст. 5 ФЗ-38.
    # Не выдумываем категорию или specific-объект — пусть Stage 2 работает только
    # с универсальными правилами.
    return {
        "material_kind": "informational",
        "category": None,
        "object_identifiers": [],
        "applicable_laws": ["ФЗ-38"],
        "target_articles": [{"law": "38", "article": "5"}],
        "checklist": [
            "[ч. 3 ст. 5 ФЗ-38] Отсутствуют гарантии результата (доходности, излечения, эффективности)",
            "[ч. 3 ст. 5 ФЗ-38] Отсутствуют абсолютные характеристики без подтверждения (лучший, №1)",
            "[ч. 3 ст. 5 ФЗ-38] Сравнения с конкурентами имеют подтверждение",
            "[ч. 7 ст. 5 ФЗ-38] Раскрыты все существенные условия",
        ],
        "search_queries": [
            ad_text[:500] + "\n\nтребования к рекламе закон о рекламе ненадлежащая реклама",
        ],
    }


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
        if len(content) > MAX_UPLOAD_BYTES:
            mb = MAX_UPLOAD_BYTES // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"Файл слишком большой. Максимум {mb} МБ.",
            )
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


def _reconstruct_article(chunks: list[SearchResult]) -> str:
    """Склеивает чанки ОДНОЙ статьи обратно в непрерывный текст.

    Chunker дробит длинные статьи по пунктам для качества retrieval и при этом:
      1) префиксит continuation-чанкам строку-заголовок "Статья N..." (chunking.py),
      2) при сверхдлинном пункте дробит его SimpleChunker'ом с overlap=200.
    Эта функция убирает оба артефакта: срезает повторный заголовок и
    de-overlap дедупит стык. Порядок чанков уже верный (fetch_by_articles
    ORDER BY chunk_index), но если есть meta.chunk_index_in_article у всех —
    досортируем для надёжности. Ничего не теряем — конкатенируем всё.
    """
    if not chunks:
        return ""
    if all(isinstance(c.meta.get("chunk_index_in_article"), int) for c in chunks):
        chunks = sorted(chunks, key=lambda c: c.meta["chunk_index_in_article"])

    first_content = chunks[0].content
    # header_line — первая непустая строка первого чанка ("Статья N. ...")
    header_line = ""
    for line in first_content.splitlines():
        if line.strip():
            header_line = line.strip()
            break

    result = first_content
    for c in chunks[1:]:
        body = c.content.lstrip()
        # 1) Срезаем искусственно добавленный заголовок статьи
        if header_line and body.startswith(header_line):
            body = body[len(header_line):].lstrip("\n \t")
        # 2) De-overlap: ищем макс. пересечение хвоста result с началом body
        if body and result:
            max_k = min(300, len(body), len(result))
            for k in range(max_k, 19, -1):
                if result[-k:] == body[:k]:
                    body = body[k:]
                    break
        body = body.strip()
        if body:
            result += "\n\n" + body
    return result


def _build_structured_context(mandatory: list[SearchResult]) -> str:
    """Build context section from mandatory (direct lookup) chunks.

    Чанки группируются по (law, article) и склеиваются `_reconstruct_article`
    в непрерывную статью — LLM видит статью целиком, без повторов заголовка.
    """
    groups: dict[tuple[str, str], list[SearchResult]] = {}
    order: list[tuple[str, str]] = []
    for r in mandatory:
        key = (r.meta.get("law", ""), r.meta.get("article", ""))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r)

    parts: list[str] = []
    for i, key in enumerate(order, 1):
        law, article = key
        chunks = groups[key]
        header = f"[{i}] {law}" + (f", ст. {article}" if article else "")
        parts.append(f"{header}\n{_reconstruct_article(chunks)}")

    return "\n\n---\n\n".join(parts) if parts else "(нет)"


async def _fetch_missing_for_risks(
    repo: VectorRepository,
    risks: list[dict],
    already: list[SearchResult],
) -> list[SearchResult]:
    """Догружает из БД статьи, на которые ссылаются риски, но которых нет в already.

    Stage 2 может зафлагать норму, которую Stage 1 не запросил. Без догрузки фильтр
    в _build_all_citations найдёт 0 источников при непустом списке рисков. Этот
    хелпер закрывает разрыв. Использует multi-parser — догружаем ВСЕ упомянутые
    в риске статьи, а не только первую (риск может ссылаться на несколько норм).
    """
    if not risks:
        return []
    have_keys: set[tuple[str, str]] = {
        _chunk_law_article_key(r.meta) for r in already
    }
    needed: set[tuple[str, str]] = set()
    for risk in risks:
        if not isinstance(risk, dict):
            continue
        for parsed in _parse_law_references_all(risk.get("law_reference", "")):
            if parsed not in have_keys:
                needed.add(parsed)
    if not needed:
        return []
    target_articles = [{"law": law, "article": article} for (law, article) in needed]
    extra = await repo.fetch_by_articles(target_articles)
    logger.info(
        "[ANALYZE] refetched %d articles for risks: %s",
        len({(r.meta.get("law"), r.meta.get("article")) for r in extra}),
        sorted(needed),
    )
    return extra


def _parse_law_reference_segment(segment: str) -> tuple[str | None, str | None]:
    """Парсит один сегмент строки в (law_num, article_num). Любая часть может быть None.

    Принимает формы: "ч. 3 ст. 5 ФЗ-38", "ст. 51 ФЗ-156", "ст. 28.1 ФЗ-38",
    "ст. 5 38-ФЗ", "ст. 28" (без ФЗ → law=None), "ФЗ-38" (без ст. → article=None).

    Важно: форма `NN-ФЗ` требует именно дефис (без пробела). Иначе паттерн
    жадно ловит номер статьи из строк вида "ст. 28 ФЗ-38" → law="28" вместо 38.
    """
    if not segment:
        return (None, None)
    article_m = re.search(r"ст\.?\s*(\d+(?:[.\-]\d+)?)", segment, re.IGNORECASE)
    law_m = re.search(r"ФЗ[-\s№]*(\d+)|(\d+)-ФЗ", segment, re.IGNORECASE)
    article = re.sub(r"[^\d]", "", article_m.group(1)) if article_m else None
    law = (law_m.group(1) or law_m.group(2)) if law_m else None
    return (law or None, article or None)


def _parse_law_references_all(ref: str) -> list[tuple[str, str]]:
    """Парсит ВСЕ (law, article) пары из строки риск-references.

    Стратегия: split по `,` и `;` → для каждого segment'а вытаскиваем (law, article).
    Если в сегменте нет ФЗ-номера, наследуем последний явно указанный — это покрывает
    кейсы "ст. 5, 28 ФЗ-38" → [(38, 5), (38, 28)]. Если в сегменте нет статьи —
    skip (одинокий "ФЗ-38" без статьи нам бесполезен).
    """
    if not ref:
        return []
    segments = re.split(r"[,;]", ref)
    parsed_segments = [_parse_law_reference_segment(s) for s in segments]

    # Forward pass: для сегментов без law — берём предыдущий явно указанный
    last_law: str | None = None
    for i, (law, article) in enumerate(parsed_segments):
        if law:
            last_law = law
        elif last_law:
            parsed_segments[i] = (last_law, article)

    # Backward pass: для сегментов в начале (где предыдущего law не было) —
    # берём следующий явно указанный. Покрывает "ст. 5 и ст. 28 ФЗ-38" если LLM
    # пишет статью раньше закона.
    next_law: str | None = None
    for i in range(len(parsed_segments) - 1, -1, -1):
        law, article = parsed_segments[i]
        if law:
            next_law = law
        elif next_law:
            parsed_segments[i] = (next_law, article)

    seen: set[tuple[str, str]] = set()
    result: list[tuple[str, str]] = []
    for law, article in parsed_segments:
        if law and article and (law, article) not in seen:
            seen.add((law, article))
            result.append((law, article))
    return result


def _parse_law_reference(ref: str) -> tuple[str, str] | None:
    """Backward-compat обёртка: возвращает первый результат из multi-parser."""
    refs = _parse_law_references_all(ref)
    return refs[0] if refs else None


def _chunk_law_article_key(meta: dict) -> tuple[str, str]:
    """Нормализует meta {law, article} в (law_num, article_num) для сравнения с ссылками рисков.

    meta.law имеет вид "ФЗ 38 ФЗ 13 03 2006" → берём первое число с разумным
    диапазоном (1-999). meta.article вида "29." или "275-" → только цифры.
    """
    law_str = str(meta.get("law", ""))
    article_str = str(meta.get("article", ""))
    # Первое число из meta.law, отбрасывая годы и даты (>1000).
    law_num = ""
    for m in re.finditer(r"\d+", law_str):
        n = m.group(0)
        if 1 <= int(n) <= 999:
            law_num = n
            break
    article_num = re.sub(r"[^\d]", "", article_str)
    return (law_num, article_num)


def _build_all_citations(
    mandatory: list[SearchResult],
    risks: list[dict] | None = None,
) -> list[CitationResponse]:
    """Build citation list — ОДИН источник = ОДНА статья (склеенная целиком).

    Чанки группируются по нормализованному ключу (law_num, article_num) и
    склеиваются `_reconstruct_article` в непрерывный текст. Юзер видит одну
    карточку на статью, а не N обрывков. Фильтр оставляет только статьи на
    которые реально ссылаются риски (multi-parser ловит несколько норм в строке).
    """
    referenced: set[tuple[str, str]] = set()
    for risk in risks or []:
        if not isinstance(risk, dict):
            continue
        for parsed in _parse_law_references_all(risk.get("law_reference", "")):
            referenced.add(parsed)

    # Группируем по (law_num, article_num), сохраняя порядок первого появления.
    groups: dict[tuple[str, str], list[SearchResult]] = {}
    order: list[tuple[str, str]] = []
    for r in mandatory:
        k = _chunk_law_article_key(r.meta)
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(r)

    def _make(chunks: list[SearchResult]) -> CitationResponse:
        first = chunks[0]
        return CitationResponse(
            chunk_id=first.chunk_id,
            document_id=first.document_id,
            content=_reconstruct_article(chunks),
            retrieval_score=max(c.score for c in chunks),
            meta=first.meta,
        )

    if referenced:
        result = [_make(groups[k]) for k in order if k in referenced]
        if result:
            return result
        # Битый law_reference от LLM → fallback на все статьи mandatory.

    return [_make(groups[k]) for k in order]


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

    mandatory = await repo.fetch_by_articles(classification.get("target_articles", []))
    mandatory_ctx = _build_structured_context(mandatory)

    checklist_str = _format_checklist(classification.get("checklist", []))
    user_msg = AD_ANALYSIS_USER_TEMPLATE.format(
        material_kind=classification.get("material_kind", "не определён"),
        category=classification.get("category") or "не применимо",
        object_identifiers=_format_object_identifiers(classification.get("object_identifiers", [])),
        found_attributes=_format_found_attributes(classification.get("found_attributes", {})),
        applicable_laws=", ".join(classification.get("applicable_laws", ["ФЗ-38"])),
        checklist=checklist_str,
        ad_text=ad_text,
        mandatory_context=mandatory_ctx,
    )

    logger.info(
        "[ANALYZE] material_kind=%s category=%s mandatory_articles=%d",
        classification.get("material_kind"),
        classification.get("category"),
        len({(r.meta.get("law"), r.meta.get("article")) for r in mandatory}),
    )

    parsed, raw = await _analyze_stage2(llm, AD_ANALYSIS_SYSTEM_PROMPT, user_msg)
    logger.info("[ANALYZE] LLM raw output:\n%s", raw)

    risks = parsed.get("risks", [])
    logger.info(
        "analyze_completed",
        extra={
            "overall": parsed.get("overall_risk_level"),
            "risks_count": len(risks),
            "category": classification.get("category"),
        },
    )

    # Догружаем статьи, упомянутые в рисках, но отсутствующие в mandatory.
    extra_chunks = await _fetch_missing_for_risks(repo, risks, mandatory)
    full_mandatory = list(mandatory) + extra_chunks

    return AnalyzeResponse(
        risks=risks,
        summary=parsed.get("summary", raw),
        overall_risk_level=parsed.get("overall_risk_level", "unknown"),
        citations=_build_all_citations(full_mandatory, risks),
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
        # Таймер для эксперимента H3: middleware обрезает время на возврате
        # Response, не на закрытии стрима, поэтому замеряем явно внутри generate.
        _t0 = time.perf_counter()

        def _event(payload: dict) -> str:
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # Извлечённый текст материала — фронт использует для inline-подсветки фрагментов риска
        yield _event({"type": "ad_text", "text": ad_text})

        yield _event({"type": "thinking", "text": "Определяю категорию и применимые нормы..."})

        classification = await _classify_ad(llm, ad_text)
        thinking_label = _humanize_classification(classification)
        yield _event({"type": "thinking", "text": f"{thinking_label}. Загружаю нормативные акты..."})

        mandatory = await repo.fetch_by_articles(classification.get("target_articles", []))
        total = len({(r.meta.get("law", ""), r.meta.get("article", "")) for r in mandatory})
        yield _event({"type": "thinking", "text": f"Загружено {total} статей. Анализирую на соответствие..."})

        mandatory_ctx = _build_structured_context(mandatory)
        logger.info(
            "[ANALYZE] material_kind=%s category=%s mandatory_articles=%d",
            classification.get("material_kind"),
            classification.get("category"),
            total,
        )

        checklist_str = _format_checklist(classification.get("checklist", []))
        user_msg = AD_ANALYSIS_USER_TEMPLATE.format(
            material_kind=classification.get("material_kind", "не определён"),
            category=classification.get("category") or "не применимо",
            object_identifiers=_format_object_identifiers(classification.get("object_identifiers", [])),
            found_attributes=_format_found_attributes(classification.get("found_attributes", {})),
            applicable_laws=", ".join(classification.get("applicable_laws", ["ФЗ-38"])),
            checklist=checklist_str,
            ad_text=ad_text,
            mandatory_context=mandatory_ctx,
        )

        # Per-risk streaming: каждый завершённый объект из массива risks летит
        # на фронт как отдельное `risk`-событие, юзер видит карточки появляющимися
        # по одной (UX-задержка до первого риска ~5-8 сек вместо 15-25 сек).
        risks: list[dict] = []
        summary = ""
        overall = "unknown"
        async for ev_type, payload in _analyze_stage2_stream(llm, AD_ANALYSIS_SYSTEM_PROMPT, user_msg):
            if ev_type == "risk":
                risks.append(payload)
                yield _event({"type": "risk", "data": payload})
            elif ev_type == "done":
                summary = payload.get("summary", "") or ""
                overall = payload.get("overall_risk_level", "unknown") or "unknown"
                yield _event({"type": "result_meta", "summary": summary, "overall_risk_level": overall})

        logger.info(
            "analyze_completed",
            extra={
                "overall": overall,
                "risks_count": len(risks),
                "category": classification.get("category"),
                "material_kind": classification.get("material_kind"),
            },
        )

        # Backward-compat: финальный агрегированный result для оркестратора (он его
        # сохранит в БД). Фронт игнорит если уже видел `risk`-события.
        yield _event({"type": "result", "data": {
            "risks": risks,
            "summary": summary,
            "overall_risk_level": overall,
        }})

        # Догружаем статьи, упомянутые в рисках, но отсутствующие в выгруженных чанках.
        extra_chunks = await _fetch_missing_for_risks(repo, risks, mandatory)
        full_mandatory = list(mandatory) + extra_chunks

        citations_data = [c.model_dump() for c in _build_all_citations(full_mandatory, risks)]
        yield _event({"type": "citations", "data": citations_data})
        yield "data: [DONE]\n\n"

        total_ms = int((time.perf_counter() - _t0) * 1000)
        logger.info("analyze_total_ms", extra={"total_ms": total_ms})

    return StreamingResponse(generate(), media_type="text/event-stream")


def _format_checklist(items: list[str]) -> str:
    if items:
        return "\n".join(f"- {item}" for item in items)
    return "- Общие требования ФЗ-38"


def _format_object_identifiers(items: list) -> str:
    """Format identifiers list for Stage 2 prompt — comma-joined or 'не указаны'."""
    if not items or not isinstance(items, list):
        return "не указаны (информационный/обзорный материал)"
    cleaned = [str(x).strip() for x in items if str(x).strip()]
    if not cleaned:
        return "не указаны (информационный/обзорный материал)"
    return ", ".join(cleaned)


# Человекочитаемые лейблы для атрибутов в Stage 2 user-template.
_ATTR_LABELS = {
    "license_number": "Номер лицензии",
    "company_name": "Наименование компании / УК",
    "company_address": "Юридический адрес",
    "company_phone": "Телефон",
    "company_website": "Сайт / домен",
    "rules_registration": "Регистрация правил ДУ (номер/дата)",
    "info_disclosure_address": "Адрес инфо-центра раскрытия",
    "advertising_label": "Пометка 'РЕКЛАМА'",
    "risk_disclaimer": "Оговорка о рисках / прошлых периодах",
}


def _format_found_attributes(attrs: dict) -> str:
    """Форматирует found_attributes в читаемый блок для Stage 2.

    Пишет ТОЛЬКО присутствующие (не-null) атрибуты, чтобы Stage 2 видел
    что уже найдено и не дублировал их в risks как "отсутствует". Если
    ничего не найдено — возвращает явное "(нет идентифицированных реквизитов)".
    """
    if not isinstance(attrs, dict) or not attrs:
        return "(нет идентифицированных реквизитов)"
    lines: list[str] = []
    for key, label in _ATTR_LABELS.items():
        val = attrs.get(key)
        if val and isinstance(val, str) and val.strip() and val.lower() != "null":
            lines.append(f"- {label}: {val.strip()}")
    if not lines:
        return "(нет идентифицированных реквизитов)"
    return "\n".join(lines)


# Человекочитаемые лейблы для UI thinking-стрима.
_MATERIAL_KIND_RU = {
    "commercial_advertising": "Реклама конкретного объекта",
    "informational": "Информационный/обзорный материал",
    "mixed": "Смешанный материал",
}

_CATEGORY_RU = {
    "alcohol": "алкоголь",
    "tobacco": "табак",
    "medicines": "лекарства",
    "bad": "БАД",
    "sports_nutrition": "спортивное питание",
    "medical_services": "медицинские услуги",
    "financial_services": "финансовые услуги",
    "securities": "ценные бумаги / ПИФ",
    "real_estate": "недвижимость",
    "gambling": "игорный бизнес",
    "child_products": "детские товары",
    "food": "пищевые продукты",
    "general_services": "услуги (общие)",
    "general_goods": "товары (общие)",
    "other": "иная категория",
}


def _humanize_classification(classification: dict) -> str:
    """Build human-readable classification label for UI thinking events.

    Examples:
      - "Информационный/обзорный материал"
      - "Реклама конкретного объекта (финансовые услуги)"
    """
    kind = classification.get("material_kind") or ""
    category = classification.get("category")
    kind_label = _MATERIAL_KIND_RU.get(kind, "Материал не классифицирован")
    if category and isinstance(category, str):
        cat_label = _CATEGORY_RU.get(category, category)
        return f"{kind_label} ({cat_label})"
    return kind_label


def _parse_json(raw: str) -> dict:
    """Try to parse LLM output as JSON, handling markdown code blocks.

    Если стандартный парсинг упал (GigaChat изредка эмитит лишний `\\"`
    посреди string-полей), пробуем восстановить структуру вручную через
    `_recover_analysis()` — анализ модели уже сделан, незачем ретраить.

    Recovery-ветви (bracket_slice + regex-recovery) обёрнуты под флаг
    settings.analyze_recovery_enabled (см. config). При false остаётся
    только стандартный json.loads — это baseline для эксперимента H1.
    Каждый исход парсинга логируется как `parse_event` с полем
    parse_path ∈ {json_loads_ok, bracket_slice_ok, regex_recovery_ok,
    total_failure}.
    """
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n", 1)
        text = lines[1] if len(lines) > 1 else text
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        result = json.loads(text)
        logger.info("parse_event", extra={"parse_path": "json_loads_ok"})
        return result
    except json.JSONDecodeError:
        pass

    if not settings.analyze_recovery_enabled:
        logger.info("parse_event", extra={"parse_path": "total_failure"})
        return {}

    # Recovery шаг 1: попытка извлечь содержимое между первой и последней
    # фигурной скобкой. Помогает, когда модель добавила лишние комментарии
    # до или после json.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start:end + 1])
            logger.info("parse_event", extra={"parse_path": "bracket_slice_ok"})
            return result
        except json.JSONDecodeError:
            pass

    # Recovery шаг 2: regex-парсер по структуре риска. Толерантен к
    # лишним `\"` внутри строковых значений.
    recovered = _recover_analysis(text)
    if recovered:
        logger.warning(
            "[PARSE] standard JSON failed, recovered %d risks from malformed output",
            len(recovered.get("risks", [])),
        )
        logger.info("parse_event", extra={"parse_path": "regex_recovery_ok"})
        return recovered

    logger.warning(
        "[PARSE] failed to parse LLM JSON, raw_len=%d head=%r tail=%r",
        len(raw),
        raw[:200],
        raw[-200:],
    )
    logger.info("parse_event", extra={"parse_path": "total_failure"})
    return {}


_RISK_FIELDS = ("fragment", "law_reference", "risk_level", "description", "suggestion")


def _recover_analysis(text: str) -> dict:
    """Вытаскивает risks/summary/overall_risk_level из битого LLM-вывода.

    Стратегия: вместо парсинга всего объекта целиком, сканируем text и для
    каждого поля каждого риска вытаскиваем значение по паттерну
    `"field": "..."` с хвостовым закрывающим `"` перед `,` или `\\n`.
    Это толерантнее к лишним `\\"` внутри значения чем json.loads.
    """
    risks: list[dict] = []
    # Бьём text на блоки по `"fragment":` — каждое появление = новый риск.
    parts = re.split(r'"fragment"\s*:\s*', text)[1:]
    for part in parts:
        risk: dict = {}
        # fragment — первое поле, его значение в начале текущего part.
        frag = _extract_string_value(part)
        if not frag:
            continue
        risk["fragment"] = frag
        for field in _RISK_FIELDS[1:]:
            m = re.search(rf'"{field}"\s*:\s*', part)
            if not m:
                continue
            val = _extract_string_value(part[m.end():])
            if val:
                risk[field] = val
        # Минимум должен быть fragment + хотя бы description или risk_level.
        if "description" in risk or "risk_level" in risk:
            risks.append(risk)

    if not risks:
        return {}

    # summary и overall — best-effort, не критичны.
    summary = ""
    m = re.search(r'"summary"\s*:\s*', text)
    if m:
        summary = _extract_string_value(text[m.end():]) or ""
    overall = "high"  # дефолт безопасный — раз есть риски, не ставить low
    m = re.search(r'"overall_risk_level"\s*:\s*"(low|medium|high)"', text)
    if m:
        overall = m.group(1)

    return {"risks": risks, "summary": summary, "overall_risk_level": overall}


def _extract_string_value(s: str) -> str:
    """Достаёт значение JSON-строки, начиная с `"` в s.

    Толерантно к лишним `\\"` внутри: ищем закрывающий `"` который идёт
    перед `,`, `\\n`, или `}` (т.е. структурным разделителем).
    """
    s = s.lstrip()
    if not s.startswith('"'):
        return ""
    # Ищем закрывающую кавычку, за которой следует структурный разделитель.
    # Это `"` + опц. пробелы/перевод + `,` или `}` или `\n  "` (next field).
    m = re.search(r'"\s*(?:,|\}|\n\s*"|$)', s[1:])
    if not m:
        return ""
    inner = s[1:1 + m.start()]
    # Распаковываем стандартные escape'ы. Лишние `\"` внутри теперь просто `"`.
    inner = inner.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
    return inner.strip()


async def _analyze_stage2(
    llm: LLMProvider, system: str, user: str,
) -> tuple[dict, str]:
    """Stage 2 с recovery + один ретрай если совсем ничего не вытащили.

    Порядок защиты:
      1) llm.complete → _parse_json (json.loads → fallback → recovery)
      2) если risks пуст — ретрай. Это покрывает редкий случай когда
         модель вернула не-JSON или совершенно битую структуру где даже
         regex-recovery не нашёл ни одного `"fragment":`.

    Retry также обёрнут под settings.analyze_recovery_enabled — это нужно,
    чтобы baseline-режим эксперимента H1 был чистым (только json.loads,
    без любых дополнительных слоёв защиты).
    """
    raw = await llm.complete(system=system, user=user)
    parsed = _parse_json(raw)
    if parsed.get("risks"):
        return parsed, raw
    if not settings.analyze_recovery_enabled:
        # Baseline-режим: ретрай отключён, возвращаем то, что получили.
        return parsed, raw
    logger.warning("[ANALYZE] empty risks after parse+recovery, retrying once")
    raw2 = await llm.complete(system=system, user=user)
    parsed2 = _parse_json(raw2)
    if parsed2.get("risks"):
        logger.info("[ANALYZE] retry succeeded with %d risks", len(parsed2["risks"]))
        logger.info("parse_event", extra={"parse_path": "retry_ok"})
        return parsed2, raw2
    # Возвращаем что есть (возможно пустое) — клиент увидит {} и поймёт что не сработало.
    return parsed or parsed2, raw2 if parsed2 else raw


def _extract_complete_risks(buffer: str, emitted_count: int) -> list[dict]:
    """Извлекает завершённые JSON-объекты из массива `"risks": [...]` стримящегося буфера.

    Сканер: state machine с двумя счётчиками — depth для балансных {}
    и in_string флаг. Внутри string content игнорим скобки (важно для случая
    когда description содержит `{` или `}` в свободном тексте). Учитываем
    escape-последовательности типа `\\"`.

    Возвращает только новые риски (skipping первые emitted_count). Идемпотентна
    на одинаковом (buffer, emitted_count) — даёт пустой список если новых нет.
    """
    m = re.search(r'"risks"\s*:\s*\[', buffer)
    if not m:
        return []

    completed_blocks: list[str] = []
    pos = m.end()
    depth = 0
    in_string = False
    object_start = -1
    n = len(buffer)

    while pos < n:
        c = buffer[pos]
        if in_string:
            if c == '\\':
                pos += 2  # пропускаем escape-пару (\", \\, \n и т.п.)
                continue
            if c == '"':
                in_string = False
            pos += 1
            continue
        # outside string
        if c == '"':
            in_string = True
        elif c == '{':
            if depth == 0:
                object_start = pos
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and object_start != -1:
                completed_blocks.append(buffer[object_start:pos + 1])
                object_start = -1
        elif c == ']' and depth == 0:
            # Конец массива risks — останавливаемся
            break
        pos += 1

    new_blocks = completed_blocks[emitted_count:]
    results: list[dict] = []
    for block in new_blocks:
        try:
            risk = json.loads(block)
            if isinstance(risk, dict):
                results.append(risk)
        except json.JSONDecodeError:
            recovered = _recover_single_risk(block)
            if recovered:
                results.append(recovered)
    return results


def _recover_single_risk(block: str) -> dict | None:
    """Извлекает поля одного риска регэкспом (для битого escaping внутри строк).

    Минимум должен быть fragment + (description ИЛИ risk_level), иначе
    считаем что блок не риск.
    """
    risk: dict = {}
    for field in _RISK_FIELDS:
        m = re.search(rf'"{field}"\s*:\s*', block)
        if not m:
            continue
        val = _extract_string_value(block[m.end():])
        if val:
            risk[field] = val
    if "fragment" in risk and ("description" in risk or "risk_level" in risk):
        return risk
    return None


async def _analyze_stage2_stream(
    llm: LLMProvider, system: str, user: str,
):
    """Stream-версия Stage 2 — async generator событий для SSE.

    Yields:
      ("risk", dict) — каждый новый завершённый объект из массива risks
      ("done", {summary, overall_risk_level, raw, risks_total}) — финал

    Retry-fallback: если стрим дал 0 рисков (LLM странно построил JSON или
    стрим оборвался) — делаем один retry через non-streaming complete().
    Это гарантирует отсутствие дубликатов (мы НЕ дополняем уже эмитированных).
    """
    buffer = ""
    emitted = 0
    stream_failed = False

    try:
        async for chunk in llm.stream(system=system, user=user):
            buffer += chunk
            new_risks = _extract_complete_risks(buffer, emitted)
            for risk in new_risks:
                emitted += 1
                yield ("risk", risk)
    except Exception as exc:
        logger.warning("[ANALYZE] stage 2 stream failed: %s", exc)
        stream_failed = True

    logger.info("[ANALYZE] stage 2 stream raw output (len=%d):\n%s", len(buffer), buffer)

    # Парсим полный буфер для summary/overall.
    parsed = _parse_json(buffer) if buffer else {}

    # Retry-fallback: 0 рисков (или стрим упал и не успел ничего эмитнуть).
    if emitted == 0 and settings.analyze_recovery_enabled:
        logger.warning("[ANALYZE] stream emitted 0 risks (failed=%s), falling back to non-streaming retry", stream_failed)
        try:
            raw_retry = await llm.complete(system=system, user=user)
            logger.info("[ANALYZE] retry raw output:\n%s", raw_retry)
            parsed_retry = _parse_json(raw_retry)
            for risk in parsed_retry.get("risks", []):
                emitted += 1
                yield ("risk", risk)
            parsed = parsed_retry
            buffer = raw_retry
            if emitted > 0:
                logger.info("[ANALYZE] retry succeeded with %d risks", emitted)
                logger.info("parse_event", extra={"parse_path": "stream_retry_ok"})
        except Exception as exc:
            logger.error("[ANALYZE] retry also failed: %s", exc)

    yield ("done", {
        "summary": parsed.get("summary", ""),
        "overall_risk_level": parsed.get("overall_risk_level", "unknown"),
        "raw": buffer,
        "risks_total": emitted,
    })
