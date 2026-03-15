from __future__ import annotations

import asyncpg
from fastapi import Header, HTTPException

from app.config import settings
from app.core.embeddings import BaseEmbedder, GigaChatEmbedder, YandexEmbedder
from app.core.retrieval import HybridRetriever
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.storage.pgvector import VectorRepository, create_pool

# ---------------------------------------------------------------------------
# Singletons — initialised in lifespan (see main.py)
# ---------------------------------------------------------------------------

_pool: asyncpg.Pool | None = None
_embedder: BaseEmbedder | None = None
_llm: LLMProvider | None = None


def _build_embedder() -> BaseEmbedder:
    provider = settings.embedding_provider.lower()
    if provider == "gigachat":
        if not settings.gigachat_client_id or not settings.gigachat_client_secret:
            raise RuntimeError(
                "GIGACHAT_CLIENT_ID and GIGACHAT_CLIENT_SECRET must be set "
                "when EMBEDDING_PROVIDER=gigachat"
            )
        return GigaChatEmbedder(
            client_id=settings.gigachat_client_id,
            client_secret=settings.gigachat_client_secret,
        )
    if provider == "yandex":
        if not settings.yandex_folder_id or not settings.yandex_api_key:
            raise RuntimeError(
                "YANDEX_FOLDER_ID and YANDEX_API_KEY must be set "
                "when EMBEDDING_PROVIDER=yandex"
            )
        return YandexEmbedder(
            folder_id=settings.yandex_folder_id,
            api_key=settings.yandex_api_key,
        )
    raise ValueError(f"Unknown embedding provider: {provider!r}. Supported: gigachat, yandex")


async def init_dependencies() -> None:
    global _pool, _embedder, _llm
    _pool = await create_pool(settings.database_url)
    _embedder = _build_embedder()
    _llm = get_llm_provider(settings)


async def close_dependencies() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ---------------------------------------------------------------------------
# FastAPI dependency functions
# ---------------------------------------------------------------------------


def get_vector_repo() -> VectorRepository:
    if _pool is None:
        raise RuntimeError("Database pool not initialised")
    return VectorRepository(_pool)


def get_embedder() -> BaseEmbedder:
    if _embedder is None:
        raise RuntimeError("Embedder not initialised")
    return _embedder


def get_retriever() -> HybridRetriever:
    return HybridRetriever(get_vector_repo(), get_embedder())


def get_llm() -> LLMProvider:
    if _llm is None:
        raise RuntimeError("LLM provider not initialised")
    return _llm


async def verify_ingest_key(x_api_key: str = Header(...)) -> None:
    if not settings.ingest_api_key:
        return  # key protection disabled — dev mode
    if x_api_key != settings.ingest_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
