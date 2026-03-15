from __future__ import annotations

import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def complete(self, system: str, user: str, max_tokens: int = 2048) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        async with await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            stream=True,
        ) as resp:
            async for chunk in resp:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
