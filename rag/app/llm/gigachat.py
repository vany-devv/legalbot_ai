from __future__ import annotations

import asyncio
import base64
import logging
import time
from typing import AsyncIterator

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


class GigaChatAuth:
    """Thread-safe OAuth token manager for GigaChat."""

    def __init__(self, client_id: str, client_secret: str) -> None:
        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        self._auth_header = f"Basic {credentials}"
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        async with self._lock:
            if self._token and time.time() < self._expires_at - 30:
                return self._token
            self._token, self._expires_at = await self._fetch_token()
            return self._token

    async def _fetch_token(self) -> tuple[str, float]:
        async with httpx.AsyncClient(verify=False, timeout=15) as client:
            resp = await client.post(
                _AUTH_URL,
                headers={
                    "Authorization": self._auth_header,
                    "RqUID": _new_uuid(),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"scope": "GIGACHAT_API_PERS"},
            )
            resp.raise_for_status()
            data = resp.json()
            token = data["access_token"]
            expires_at = data.get("expires_at", 0) / 1000.0
            if expires_at == 0:
                expires_at = time.time() + 1800
            logger.debug("GigaChat token refreshed, expires at %s", expires_at)
            return token, expires_at


class GigaChatProvider(LLMProvider):
    def __init__(self, client_id: str, client_secret: str, model: str = "GigaChat-Pro") -> None:
        self._auth = GigaChatAuth(client_id, client_secret)
        self._model = model

    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def complete(self, system: str, user: str, max_tokens: int = 2048) -> str:
        token = await self._auth.get_token()
        async with httpx.AsyncClient(verify=False, timeout=60) as client:
            resp = await client.post(
                _API_URL,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": max_tokens,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        token = await self._auth.get_token()
        async with httpx.AsyncClient(verify=False, timeout=120) as client:
            async with client.stream(
                "POST",
                _API_URL,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    import json

                    data = json.loads(payload)
                    delta = data["choices"][0].get("delta", {}).get("content", "")
                    if delta:
                        yield delta


def _new_uuid() -> str:
    import uuid

    return str(uuid.uuid4())
