from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM
    llm_provider: str = "gigachat"
    gigachat_client_id: str = ""
    gigachat_client_secret: str = ""
    gigachat_model: str = "GigaChat-Pro"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/legalbot"

    # Security
    ingest_api_key: str = ""

    # RAG parameters
    default_top_k: int = 8
    chunk_max_len: int = 1000
    chunk_overlap: int = 150

    # Embeddings — provider: "gigachat" | "yandex"
    embedding_provider: str = "yandex"
    embedding_dim: int = 256               # 256 for yandex, 1024 for gigachat

    # Yandex Cloud
    yandex_folder_id: str = ""
    yandex_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
