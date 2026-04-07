from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.answer import _build_context, _citations
from app.api.ingest import _extract_text
from app.api.schemas import AnalyzeResponse
from app.core.retrieval import HybridRetriever
from app.dependencies import get_llm, get_retriever
from app.llm.base import LLMProvider
from app.prompts.advertising import AD_ANALYSIS_SYSTEM_PROMPT, AD_ANALYSIS_USER_TEMPLATE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["analyze"])

MAX_AD_TEXT_LEN = 15_000


def _derive_search_query(ad_text: str) -> str:
    """Build a RAG search query from ad text + advertising law keywords."""
    snippet = ad_text[:500]
    return snippet + "\n\nреклама ненадлежащая реклама закон о рекламе 38-ФЗ требования ограничения"


async def _resolve_ad_text(
    text: str | None, file: UploadFile | None,
) -> str:
    """Extract ad text from either form field or uploaded file."""
    if file is not None:
        content = await file.read()
        extracted = _extract_text(content, file.filename or "upload.txt")
        if not extracted.strip():
            raise HTTPException(status_code=422, detail="Could not extract text from file")
        return extracted
    if text:
        return text
    raise HTTPException(status_code=422, detail="Provide either 'text' or 'file'")


@router.post("", response_model=AnalyzeResponse)
async def analyze(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    top_k: int = Form(default=10),
    retriever: HybridRetriever = Depends(get_retriever),
    llm: LLMProvider = Depends(get_llm),
) -> AnalyzeResponse:
    ad_text = await _resolve_ad_text(text, file)
    if len(ad_text) > MAX_AD_TEXT_LEN:
        ad_text = ad_text[:MAX_AD_TEXT_LEN]

    search_query = _derive_search_query(ad_text)
    results = await retriever.search(search_query, top_k=top_k)
    context = _build_context(results)

    user_msg = AD_ANALYSIS_USER_TEMPLATE.format(ad_text=ad_text, context=context)
    raw = await llm.complete(system=AD_ANALYSIS_SYSTEM_PROMPT, user=user_msg)

    parsed = _parse_analysis_json(raw)
    return AnalyzeResponse(
        risks=parsed.get("risks", []),
        summary=parsed.get("summary", raw),
        overall_risk_level=parsed.get("overall_risk_level", "unknown"),
        citations=_citations(results),
    )


@router.post("/stream")
async def analyze_stream(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    top_k: int = Form(default=10),
    retriever: HybridRetriever = Depends(get_retriever),
    llm: LLMProvider = Depends(get_llm),
) -> StreamingResponse:
    ad_text = await _resolve_ad_text(text, file)
    if len(ad_text) > MAX_AD_TEXT_LEN:
        ad_text = ad_text[:MAX_AD_TEXT_LEN]

    search_query = _derive_search_query(ad_text)
    results = await retriever.search(search_query, top_k=top_k)
    context = _build_context(results)

    user_msg = AD_ANALYSIS_USER_TEMPLATE.format(ad_text=ad_text, context=context)
    all_citations = _citations(results)

    async def generate():
        full_answer: list[str] = []
        async for delta in llm.stream(system=AD_ANALYSIS_SYSTEM_PROMPT, user=user_msg):
            full_answer.append(delta)
            yield f"data: {json.dumps({'type': 'delta', 'data': delta}, ensure_ascii=False)}\n\n"

        citations_data = [c.model_dump() for c in all_citations]
        yield f"data: {json.dumps({'type': 'citations', 'data': citations_data}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def _parse_analysis_json(raw: str) -> dict:
    """Try to parse LLM output as JSON, handling markdown code blocks."""
    text = raw.strip()
    # Strip markdown code block if present
    if text.startswith("```"):
        lines = text.split("\n", 1)
        text = lines[1] if len(lines) > 1 else text
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
    return {}
