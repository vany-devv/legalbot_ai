from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.schemas import CitationResponse, SearchRequest, SearchResponse
from app.core.retrieval import HybridRetriever
from app.dependencies import get_retriever

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(
    req: SearchRequest,
    retriever: HybridRetriever = Depends(get_retriever),
) -> SearchResponse:
    results = await retriever.search(req.query, top_k=req.top_k)
    return SearchResponse(
        results=[
            CitationResponse(
                chunk_id=r.chunk_id,
                document_id=r.document_id,
                content=r.content,
                retrieval_score=r.score,
                meta=r.meta,
            )
            for r in results
        ]
    )
