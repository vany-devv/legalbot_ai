from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    chunk_id: str
    document_id: str
    content: str
    score: float
    meta: dict


def _rrf(
    dense: list[SearchResult],
    sparse: list[SearchResult],
    top_k: int,
    k: int = 60,
) -> list[SearchResult]:
    """Reciprocal Rank Fusion: score(d) = Σ 1 / (k + rank_i(d))."""
    scores: dict[str, float] = {}
    by_id: dict[str, SearchResult] = {}

    for rank, result in enumerate(dense):
        scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + 1.0 / (k + rank + 1)
        by_id[result.chunk_id] = result

    for rank, result in enumerate(sparse):
        scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + 1.0 / (k + rank + 1)
        by_id[result.chunk_id] = result

    if not scores:
        return []

    max_score = max(scores.values())
    sorted_ids = sorted(scores, key=scores.__getitem__, reverse=True)[:top_k]

    results = []
    for cid in sorted_ids:
        item = by_id[cid]
        item.score = scores[cid] / max_score if max_score > 0 else 0.0
        results.append(item)
    return results


class HybridRetriever:
    """Combines dense (pgvector HNSW) and sparse (Russian FTS) search via RRF."""

    def __init__(self, vector_repo, embedder) -> None:
        self._repo = vector_repo
        self._embedder = embedder

    async def search(self, query: str, top_k: int = 8) -> list[SearchResult]:
        embedding = await self._embedder.embed_query(query)

        dense_raw, sparse_raw = await _gather_searches(
            self._repo, embedding, query, top_k
        )

        results = _rrf(dense_raw, sparse_raw, top_k=top_k)
        logger.debug("Hybrid search returned %d results for query: %.60s", len(results), query)
        return results


async def _gather_searches(repo, embedding: np.ndarray, query: str, top_k: int):
    import asyncio

    dense_task = asyncio.create_task(repo.dense_search(embedding, top_k * 2))
    sparse_task = asyncio.create_task(repo.fts_search(query, top_k * 2))
    dense_raw, sparse_raw = await asyncio.gather(dense_task, sparse_task)
    return dense_raw, sparse_raw
