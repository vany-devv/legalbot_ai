from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector

from app.core.retrieval import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class ChunkData:
    index: int
    content: str
    embedding: np.ndarray
    meta: dict


class VectorRepository:
    """Async repository backed by PostgreSQL + pgvector."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    async def add_document(
        self,
        source_id: str,
        title: str,
        doc_type: str,
        year: int | None = None,
        meta: dict | None = None,
    ) -> UUID:
        """Upsert a document and return its UUID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO rag_documents (source_id, title, doc_type, year, meta, updated_at)
                VALUES ($1, $2, $3, $4, $5::jsonb, NOW())
                ON CONFLICT (source_id) DO UPDATE
                    SET title      = EXCLUDED.title,
                        doc_type   = EXCLUDED.doc_type,
                        year       = EXCLUDED.year,
                        meta       = EXCLUDED.meta,
                        updated_at = NOW()
                RETURNING id
                """,
                source_id,
                title,
                doc_type,
                year,
                _json(meta),
            )
        return row["id"]

    async def list_documents(self) -> list[dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    d.id::text   AS id,
                    d.source_id,
                    d.title,
                    d.doc_type,
                    d.year,
                    d.updated_at,
                    COUNT(c.id)  AS chunk_count
                FROM rag_documents d
                LEFT JOIN rag_chunks c ON c.document_id = d.id
                GROUP BY d.id, d.source_id, d.title, d.doc_type, d.year, d.updated_at
                ORDER BY d.updated_at DESC
                """
            )
        return [dict(r) for r in rows]

    async def delete_document(self, source_id: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM rag_documents WHERE source_id = $1", source_id
            )
        return result != "DELETE 0"

    # ------------------------------------------------------------------
    # Chunks
    # ------------------------------------------------------------------

    async def add_chunks(self, document_id: UUID, chunks: list[ChunkData]) -> int:
        """Replace all chunks for a document and insert new ones."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "DELETE FROM rag_chunks WHERE document_id = $1", document_id
                )
                await conn.executemany(
                    """
                    INSERT INTO rag_chunks (document_id, chunk_index, content, embedding, meta)
                    VALUES ($1, $2, $3, $4, $5::jsonb)
                    """,
                    [
                        (
                            document_id,
                            c.index,
                            c.content,
                            c.embedding,
                            _json(c.meta),
                        )
                        for c in chunks
                    ],
                )
        return len(chunks)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def dense_search(
        self, embedding: np.ndarray, top_k: int = 16
    ) -> list[SearchResult]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    rc.id::text            AS chunk_id,
                    rc.document_id::text   AS document_id,
                    rc.content,
                    rc.meta,
                    1 - (rc.embedding <=> $1::vector) AS score
                FROM rag_chunks rc
                WHERE rc.embedding IS NOT NULL
                ORDER BY rc.embedding <=> $1::vector
                LIMIT $2
                """,
                embedding,
                top_k,
            )
        return [_row_to_result(r) for r in rows]

    async def fts_search(self, query: str, top_k: int = 16) -> list[SearchResult]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    rc.id::text            AS chunk_id,
                    rc.document_id::text   AS document_id,
                    rc.content,
                    rc.meta,
                    ts_rank(
                        to_tsvector('russian', rc.content),
                        plainto_tsquery('russian', $1)
                    ) AS score
                FROM rag_chunks rc
                WHERE to_tsvector('russian', rc.content) @@ plainto_tsquery('russian', $1)
                ORDER BY score DESC
                LIMIT $2
                """,
                query,
                top_k,
            )
        return [_row_to_result(r) for r in rows]

    async def fetch_by_articles(self, article_refs: list[dict]) -> list[SearchResult]:
        """Direct lookup: fetch chunks by (law number, article number) pairs.

        article_refs format: [{"law": "156", "article": "51"}, ...]
        Uses LIKE '%<number>%' to match stored law names like "ФЗ 156 ФЗ 29 11 2001".
        Returns chunks ordered by law, article, chunk_index (preserves article text order).
        Score is set to 1.0 so these chunks always rank above retrieval results.
        """
        if not article_refs:
            return []

        conditions = []
        params: list[str] = []
        for i, ref in enumerate(article_refs):
            law_param = i * 2 + 1
            art_param = i * 2 + 2
            conditions.append(
                f"(rc.meta->>'law' LIKE '%' || ${law_param} || '%' "
                f"AND rc.meta->>'article' = ${art_param})"
            )
            params.extend([str(ref["law"]), str(ref["article"])])

        where_clause = " OR ".join(conditions)
        query = f"""
            SELECT
                rc.id::text          AS chunk_id,
                rc.document_id::text AS document_id,
                rc.content,
                rc.meta,
                1.0                  AS score
            FROM rag_chunks rc
            WHERE {where_clause}
            ORDER BY rc.meta->>'law', rc.meta->>'article', rc.chunk_index
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [_row_to_result(r) for r in rows]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def get_stats(self) -> dict:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    (SELECT COUNT(*) FROM rag_documents) AS documents,
                    (SELECT COUNT(*) FROM rag_chunks)    AS chunks
                """
            )
        return {"documents": row["documents"], "chunks": row["chunks"]}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _json(d: dict | None) -> str:
    import json

    return json.dumps(d or {})


def _row_to_result(row: asyncpg.Record) -> SearchResult:
    import json

    meta = row["meta"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    return SearchResult(
        chunk_id=row["chunk_id"],
        document_id=row["document_id"],
        content=row["content"],
        score=float(row["score"]),
        meta=meta or {},
    )


async def create_pool(database_url: str) -> asyncpg.Pool:
    """Create asyncpg pool with pgvector codec registered."""
    conn = await asyncpg.connect(database_url)
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    finally:
        await conn.close()

    pool = await asyncpg.create_pool(
        database_url,
        init=register_vector,
        min_size=2,
        max_size=10,
    )
    logger.info("Database pool created")
    return pool
