from __future__ import annotations

from app.config import Settings
from app.llm.base import LLMProvider


def get_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()

    if provider == "gigachat":
        from app.llm.gigachat import GigaChatProvider

        return GigaChatProvider(
            client_id=settings.gigachat_client_id,
            client_secret=settings.gigachat_client_secret,
            model=settings.gigachat_model,
        )

    if provider == "openai":
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )

    if provider == "alice":
        from app.llm.alice_provider import AliceProvider

        return AliceProvider(
            api_key=settings.yandex_api_key,
            folder_id=settings.yandex_folder_id,
            model=settings.alice_model,
        )

    raise ValueError(f"Unknown LLM provider: {provider!r}. Supported: gigachat, openai, alice")
