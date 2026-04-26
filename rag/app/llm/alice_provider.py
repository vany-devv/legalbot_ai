from __future__ import annotations

import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_BASE_URL = "https://ai.api.cloud.yandex.net/v1"


class AliceProvider(LLMProvider):
    def __init__(self, api_key: str, folder_id: str, model: str = "aliceai-llm/latest") -> None:
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=_BASE_URL,
            project=folder_id,
        )
        self._model = f"gpt://{folder_id}/{model}"

    async def complete(self, system: str, user: str, max_tokens: int = 2048) -> str:
        response = await self._client.responses.create(
            model=self._model,
            instructions=system,
            input=user,
            max_output_tokens=max_tokens,
        )
        return response.output_text

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        stream = await self._client.responses.create(
            model=self._model,
            instructions=system,
            input=user,
            stream=True,
        )
        async for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta
