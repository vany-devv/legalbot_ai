# LegalBot AI

Юридический чат-бот с поддержкой RAG (Retrieval-Augmented Generation) для российского рынка. Отвечает на вопросы по нормативным документам со ссылками на конкретные статьи.

## Архитектура

| Сервис | Стек | Назначение |
|--------|------|-----------|
| `frontend` | Nuxt 3, Vue 3, Tailwind | UI, стриминг ответов, управление диалогами |
| `api` | Go, net/http | Auth, биллинг, история чатов, оркестрация |
| `rag` | Python, FastAPI | Эмбеддинги, гибридный поиск, LLM |
| `postgres` | PostgreSQL 16 + pgvector | Данные и векторная база |

## Быстрый старт

### Требования

- Docker и Docker Compose

### Запуск

```bash
cp .env.example .env
# Заполните .env ключами (обязательно: JWT_SECRET, GIGACHAT_* или OPENAI_API_KEY)

docker compose up -d
```

Приложение будет доступно на `http://localhost:3000`.

## Конфигурация

Все настройки через `.env` в корне проекта. Смотрите [`.env.example`](.env.example) с описанием каждой переменной.

## Документация сервисов

- [api/README.md](api/README.md) — Go API: архитектура, запуск
- [rag/README.md](rag/README.md) — Python RAG: модели, конфигурация
- [frontend/README.md](frontend/README.md) — Nuxt: конфигурация, разработка

## License

[LICENSE](LICENSE)
