# API — Go Backend

Монолитный Go-сервис с чистой архитектурой. Обрабатывает авторизацию, биллинг, историю чатов и оркестрирует взаимодействие с RAG-сервисом.

## Архитектура

```
cmd/api/main.go          — точка входа, DI сборка
internal/
  auth/                  — регистрация, логин, JWT
  billing/               — тарифы, подписки, лимиты
  chat/                  — диалоги, сообщения, цитаты
  orchestrator/          — /api/chat/ask + SSE стриминг
  proxy/                 — проксирование к RAG (/ingest, /search)
  ragclient/             — HTTP-клиент к Python RAG
  middleware/            — JWT auth middleware
  pkg/config/            — конфигурация из env
  pkg/db/                — подключение к PostgreSQL
  pkg/migrate/           — автомиграции при старте
migrations/              — SQL-миграции (goose)
```

Каждый домен организован по слоям: `domain` → `usecase` → `repository` → `handler`, связан через `wire.go`.

## API Endpoints

### Auth
| Метод | Путь | Описание |
|-------|------|---------|
| `POST` | `/api/auth/register` | Регистрация |
| `POST` | `/api/auth/login` | Вход, возвращает JWT |
| `GET` | `/api/auth/me` | Текущий пользователь |

### Chat
| Метод | Путь | Описание |
|-------|------|---------|
| `GET` | `/api/chat/conversations` | Список диалогов |
| `POST` | `/api/chat/ask` | Вопрос (не-стриминг) |
| `POST` | `/api/chat/ask/stream` | Вопрос с SSE стримингом |
| `GET` | `/api/chat/conversations/{id}` | Диалог с историей |

### RAG (проксируется в Python)
| Метод | Путь | Описание |
|-------|------|---------|
| `POST` | `/api/rag/ingest/upload` | Загрузить документ |
| `GET` | `/api/rag/ingest/jobs/{id}` | Статус задачи инжеста |
| `GET` | `/api/rag/documents` | Список документов |
| `DELETE` | `/api/rag/documents/{source_id}` | Удалить документ |
| `POST` | `/api/rag/search` | Поиск по базе знаний |

## Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|-------------|---------|
| `PORT` | `8080` | Порт сервера |
| `DATABASE_URL` | — | PostgreSQL connection string |
| `JWT_SECRET` | — | Секрет для подписи JWT |
| `RAG_SERVICE_URL` | `http://localhost:8000` | URL Python RAG сервиса |
| `INGEST_API_KEY` | — | Ключ для защиты /ingest |
| `ENV` | `development` | Окружение |

## Локальная разработка

```bash
cd api
go mod download
go run cmd/api/main.go
```

Миграции применяются автоматически при старте.
