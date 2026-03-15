from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, max_tokens: int = 2048) -> str:
        """Return a full completion string."""

    @abstractmethod
    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        """Yield text deltas as they arrive."""
