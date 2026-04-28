# RAG — Python Service

FastAPI-сервис для работы с базой знаний: загрузка документов, построение эмбеддингов, гибридный поиск и генерация ответов через LLM.

## Архитектура

```
app/
  main.py            — FastAPI app, lifespan
  config.py          — pydantic-settings
  dependencies.py    — FastAPI DI
  api/
    ingest.py        — загрузка документов (PDF, DOCX, RTF), фоновые задачи
    answer.py        — генерация ответов, SSE стриминг
    search.py        — поиск без LLM
    documents.py     — список и удаление документов
  core/
    embeddings.py    — GigaChat + Yandex embeddings API
    chunking.py      — чанкинг с учетом структуры НПА (статьи, главы)
    retrieval.py     — гибридный поиск: dense + FTS + RRF
  llm/
    base.py          — абстрактный LLMProvider
    gigachat.py      — GigaChat (OAuth, retry, streaming)
    openai_provider.py — OpenAI
    factory.py       — get_llm_provider() из конфига
  storage/
    pgvector.py      — VectorRepository (asyncpg + pgvector)
  prompts/
    legal.py         — системный промпт для правовой области
```

## Поиск

Используется гибридный поиск с Reciprocal Rank Fusion (RRF):

1. **Dense search** — косинусное сходство по HNSW-индексу (pgvector)
2. **Full-text search** — `to_tsvector('russian', ...)` в PostgreSQL
3. **RRF** — объединение результатов по формуле `1/(k + rank)`

## Модели эмбеддингов

| Провайдер | Модель | Описание |
|----------|-------|---------|
| `gigachat` | EmbeddingsGigaR | GigaChat API, 1024-dim (по умолчанию) |
| `yandex` | YandexGPT Embeddings | API Яндекса, 256-dim |

Настраивается через `EMBEDDING_PROVIDER`.

## Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|-------------|---------|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `LLM_PROVIDER` | `gigachat` | `gigachat` или `openai` |
| `GIGACHAT_CLIENT_ID` | — | GigaChat OAuth client ID |
| `GIGACHAT_CLIENT_SECRET` | — | GigaChat OAuth client secret |
| `GIGACHAT_MODEL` | `GigaChat-Pro` | Модель GigaChat |
| `OPENAI_API_KEY` | — | OpenAI API ключ |
| `OPENAI_MODEL` | `gpt-4o-mini` | Модель OpenAI |
| `INGEST_API_KEY` | — | Ключ для защиты /ingest |
| `EMBEDDING_PROVIDER` | `gigachat` | `gigachat` или `yandex` |
| `YANDEX_FOLDER_ID` | — | Folder ID Яндекса |
| `YANDEX_API_KEY` | — | API ключ Яндекса |
| `CHUNK_MAX_LEN` | `1000` | Максимальный размер чанка |
| `DEFAULT_TOP_K` | `8` | Кол-во результатов по умолчанию |

## Загрузка документов

```bash
curl -X POST http://localhost:8000/ingest/upload \
  -H "X-API-Key: $INGEST_API_KEY" \
  -F "file=@gk_rf.pdf" \
  -F "source_id=gk_rf" \
  -F "title=Гражданский кодекс РФ" \
  -F "doc_type=kodeks"
```

Поддерживаемые форматы: `.pdf`, `.docx`, `.rtf`, `.txt`

## Локальная разработка

```bash
cd rag
uv sync
uv run uvicorn app.main:app --reload
```
