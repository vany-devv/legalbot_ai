from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import numpy as np

logger = logging.getLogger(__name__)

_GIGACHAT_EMBEDDINGS_URL = "https://gigachat.devices.sberbank.ru/api/v1/embeddings"
_GIGACHAT_EMBED_MODEL = "EmbeddingsGigaR"
_GIGACHAT_BATCH_SIZE = 64


# ---------------------------------------------------------------------------
# Base interface
# ---------------------------------------------------------------------------

class BaseEmbedder(ABC):
    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> np.ndarray:
        """Return (N, dim) float32 array for a batch of document texts."""

    @abstractmethod
    async def embed_query(self, query: str) -> np.ndarray:
        """Return (dim,) float32 array for a single query."""


# ---------------------------------------------------------------------------
# GigaChat cloud embeddings (EmbeddingsGigaR, 1024-dim)
# ---------------------------------------------------------------------------

class GigaChatEmbedder(BaseEmbedder):
    """Cloud embeddings via GigaChat API.

    Reuses GigaChatAuth for token management so no extra credentials needed —
    same GIGACHAT_CLIENT_ID / GIGACHAT_CLIENT_SECRET as the LLM.
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        from app.llm.gigachat import GigaChatAuth

        self._auth = GigaChatAuth(client_id, client_secret)

    async def _call_api(self, texts: list[str]) -> np.ndarray:
        import httpx

        token = await self._auth.get_token()
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            resp = await client.post(
                _GIGACHAT_EMBEDDINGS_URL,
                headers={"Authorization": f"Bearer {token}"},
                json={"model": _GIGACHAT_EMBED_MODEL, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            # API returns items with "index" field — sort to preserve order
            ordered = sorted(data, key=lambda x: x["index"])
            return np.array([item["embedding"] for item in ordered], dtype=np.float32)

    async def _embed_batched(self, texts: list[str]) -> np.ndarray:
        """Split large batches to respect API limits."""
        if not texts:
            return np.empty((0, 1024), dtype=np.float32)

        batches = [
            texts[i : i + _GIGACHAT_BATCH_SIZE]
            for i in range(0, len(texts), _GIGACHAT_BATCH_SIZE)
        ]
        if len(batches) == 1:
            return await self._call_api(batches[0])

        import asyncio

        results = await asyncio.gather(*[self._call_api(b) for b in batches])
        return np.concatenate(results, axis=0)

    async def embed_documents(self, texts: list[str]) -> np.ndarray:
        return await self._embed_batched(texts)

    async def embed_query(self, query: str) -> np.ndarray:
        result = await self._call_api([query])
        return result[0]


# ---------------------------------------------------------------------------
# Yandex Cloud embeddings (text-search-doc / text-search-query, 256-dim)
# ---------------------------------------------------------------------------

_YANDEX_EMBED_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
# Free tier: ~1 RPS. Keep concurrency at 1 and rely on retry backoff.
_YANDEX_MAX_CONCURRENT = 1
_YANDEX_MAX_RETRIES = 7


class YandexEmbedder(BaseEmbedder):
    """Cloud embeddings via Yandex Cloud Foundation Models API.

    Uses separate model URIs for documents vs queries — important for
    asymmetric retrieval quality (Yandex optimises each separately).
    Returns 256-dim vectors.
    Free tier rate limit ~1 RPS, so requests are serialised with retry backoff.
    """

    def __init__(self, folder_id: str, api_key: str) -> None:
        import asyncio

        self._folder_id = folder_id
        self._api_key = api_key
        self._sem = asyncio.Semaphore(_YANDEX_MAX_CONCURRENT)

    def _model_uri(self, model_type: str) -> str:
        return f"emb://{self._folder_id}/{model_type}/latest"

    async def _embed_one(self, text: str, model_type: str) -> np.ndarray:
        import asyncio
        import httpx

        async with self._sem:
            for attempt in range(_YANDEX_MAX_RETRIES):
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(
                        _YANDEX_EMBED_URL,
                        headers={"Authorization": f"Api-Key {self._api_key}"},
                        json={"modelUri": self._model_uri(model_type), "text": text},
                    )
                if resp.status_code == 429:
                    wait = 2 ** attempt  # 1, 2, 4, 8, 16, 32, 64 sec
                    logger.warning("Yandex 429 — retrying in %ds (attempt %d)", wait, attempt + 1)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                return np.array(resp.json()["embedding"], dtype=np.float32)
            resp.raise_for_status()  # last attempt failed — bubble up
            return np.array(resp.json()["embedding"], dtype=np.float32)  # unreachable

    async def embed_documents(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 256), dtype=np.float32)
        # Sequential — free tier allows ~1 RPS, concurrency=1 + retry handles bursts
        results = [await self._embed_one(t, "text-search-doc") for t in texts]
        return np.stack(results)

    async def embed_query(self, query: str) -> np.ndarray:
        return await self._embed_one(query, "text-search-query")
