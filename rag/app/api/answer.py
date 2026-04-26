from __future__ import annotations

import json
import logging
import re

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.schemas import AnswerRequest, AnswerResponse, CitationResponse
from app.core.retrieval import HybridRetriever, SearchResult
from app.dependencies import get_llm, get_retriever
from app.llm.base import LLMProvider
from app.prompts.legal import LEGAL_SYSTEM_PROMPT, LEGAL_USER_TEMPLATE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/answer", tags=["answer"])


def _build_context(results: list[SearchResult]) -> str:
    parts = []
    for i, r in enumerate(results, 1):
        law = r.meta.get("law", "")
        article = r.meta.get("article", "")
        header = f"[{i}] {law}" + (f", ст. {article}" if article else "")
        parts.append(f"{header}\n{r.content}")
    return "\n\n---\n\n".join(parts)


def _citations(results: list[SearchResult]) -> list[CitationResponse]:
    return [
        CitationResponse(
            chunk_id=r.chunk_id,
            document_id=r.document_id,
            content=r.content,
            retrieval_score=r.score,
            meta=r.meta,
        )
        for r in results
    ]


def _dedup_citations(results: list[SearchResult]) -> list[CitationResponse]:
    """Return one citation per (law, article) — highest score wins."""
    best: dict[tuple, SearchResult] = {}
    for r in results:
        key = (r.meta.get("law", r.document_id), r.meta.get("article", ""))
        if key not in best or r.score > best[key].score:
            best[key] = r
    deduped = sorted(best.values(), key=lambda r: r.score, reverse=True)
    return _citations(deduped)


def _filter_used_citations(
    answer_text: str, citations: list[CitationResponse],
) -> list[CitationResponse]:
    """Keep only citations that the LLM actually referenced in its answer."""
    answer_lower = answer_text.lower()

    # 1. Parse [N] references (context numbering used by the LLM)
    referenced_indices: set[int] = set()
    for m in re.finditer(r"\[(\d+)]", answer_text):
        referenced_indices.add(int(m.group(1)))

    # 2. Parse article numbers: "ст. 37", "статье 309", etc.
    mentioned_articles: set[str] = set()
    for m in re.finditer(r"(?:стать[яеиюей]\w*|ст\.)\s*(\d+[\d.\-]*)", answer_lower):
        mentioned_articles.add(m.group(1).rstrip("."))

    used = []
    seen_ids: set[str] = set()
    for i, c in enumerate(citations):
        # Match by [N] index (1-based)
        if (i + 1) in referenced_indices:
            if c.chunk_id not in seen_ids:
                used.append(c)
                seen_ids.add(c.chunk_id)
            continue
        # Match by article number
        article = str(c.meta.get("article", "")).rstrip(".")
        if not article or article == "preamble":
            law = c.meta.get("law", "")
            if law and law.lower() in answer_lower:
                if c.chunk_id not in seen_ids:
                    used.append(c)
                    seen_ids.add(c.chunk_id)
            continue
        if article in mentioned_articles:
            if c.chunk_id not in seen_ids:
                used.append(c)
                seen_ids.add(c.chunk_id)

    # Fallback: if nothing matched, return all
    return used if used else citations


@router.post("", response_model=AnswerResponse)
async def answer(
    req: AnswerRequest,
    retriever: HybridRetriever = Depends(get_retriever),
    llm: LLMProvider = Depends(get_llm),
) -> AnswerResponse:
    results = await retriever.search(req.query, top_k=req.top_k)
    context = _build_context(results)
    user_msg = LEGAL_USER_TEMPLATE.format(query=req.query, context=context)
    text = await llm.complete(system=LEGAL_SYSTEM_PROMPT, user=user_msg)
    all_citations = _citations(results)
    used_citations = _filter_used_citations(text, all_citations)
    return AnswerResponse(answer=text, citations=used_citations)


@router.post("/stream")
async def answer_stream(
    req: AnswerRequest,
    retriever: HybridRetriever = Depends(get_retriever),
    llm: LLMProvider = Depends(get_llm),
) -> StreamingResponse:
    results = await retriever.search(req.query, top_k=req.top_k)
    context = _build_context(results)
    user_msg = LEGAL_USER_TEMPLATE.format(query=req.query, context=context)
    all_citations = _citations(results)

    async def generate():
        # Collect full answer to filter citations
        full_answer = []
        async for delta in llm.stream(system=LEGAL_SYSTEM_PROMPT, user=user_msg):
            full_answer.append(delta)
            yield f"data: {json.dumps({'type': 'delta', 'data': delta}, ensure_ascii=False)}\n\n"

        # Send filtered citations after the answer is complete
        answer_text = "".join(full_answer)
        used_citations = _filter_used_citations(answer_text, all_citations)
        citations_data = [c.model_dump() for c in used_citations]
        yield f"data: {json.dumps({'type': 'citations', 'data': citations_data}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
