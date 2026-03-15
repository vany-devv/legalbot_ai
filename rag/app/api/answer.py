from __future__ import annotations

import json
import logging

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
    return AnswerResponse(answer=text, citations=_citations(results))


@router.post("/stream")
async def answer_stream(
    req: AnswerRequest,
    retriever: HybridRetriever = Depends(get_retriever),
    llm: LLMProvider = Depends(get_llm),
) -> StreamingResponse:
    results = await retriever.search(req.query, top_k=req.top_k)
    context = _build_context(results)
    user_msg = LEGAL_USER_TEMPLATE.format(query=req.query, context=context)
    citations_payload = json.dumps(
        [c.model_dump() for c in _citations(results)], ensure_ascii=False
    )

    async def generate():
        # First event: citations metadata
        yield f"data: {json.dumps({'type': 'citations', 'data': json.loads(citations_payload)})}\n\n"
        # Subsequent events: LLM text deltas
        async for delta in llm.stream(system=LEGAL_SYSTEM_PROMPT, user=user_msg):
            yield f"data: {json.dumps({'type': 'delta', 'data': delta}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
