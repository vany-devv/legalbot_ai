# LegalBot Services (Go Monolith)

Монолит с чистой архитектурой и низкой связностью. Каждый домен самодостаточен и легко выносится в микросервис.

## Структура

```
internal/
  auth/              # Домен авторизации
    domain/          # Бизнес-логика (entities, интерфейсы)
    usecase/         # Use cases (бизнес-операции)
    repository/      # Реализация хранилищ (Postgres)
    infrastructure/  # Внешние зависимости (JWT, bcrypt)
    handler/         # HTTP handlers
    wire.go          # Dependency injection
  billing/          # Домен биллинга
    domain/
    usecase/        # create_subscription, check_limits, record_usage
    repository/
    infrastructure/  # payment providers (stub)
    handler/
    wire.go
  chat/             # Домен истории чатов
    domain/
    usecase/        # create_conversation, save_message, get_conversation
    repository/
    handler/
    wire.go
  pkg/              # Общие утилиты (config, db, errors)
```

## Принципы

1. **Чистая архитектура**: domain → usecase → repository/handler
2. **Низкая связность**: домены общаются только через интерфейсы
3. **Dependency Injection**: wire.go в каждом домене
4. **Легкий split**: каждый домен = будущий микросервис

## Домены

### Auth
- Регистрация/логин пользователей
- JWT токены
- Сессии

### Billing
- Тарифные планы
- Подписки пользователей
- Проверка лимитов (requests, documents)
- Учет использования
- Интеграция с платежными системами (stub)

### Chat
- Диалоги пользователей
- Сообщения (user/assistant)
- Цитаты из RAG (chunk_id, source, score)
- История с полным контекстом

## Запуск

```bash
# Установка зависимостей
go mod download

# Миграции (используйте migrate или вручную)
psql $DATABASE_URL < migrations/001_create_users_and_sessions.up.sql
psql $DATABASE_URL < migrations/002_create_billing_tables.up.sql
psql $DATABASE_URL < migrations/003_create_chat_tables.up.sql

# Запуск
go run cmd/api/main.go
```

## Переменные окружения

```env
PORT=8080
DATABASE_URL=postgres://user:pass@localhost/legalbot?sslmode=disable
JWT_SECRET=your-secret-key
ENV=development
```

## API Endpoints### Auth
- `POST /api/auth/register` - регистрация
- `POST /api/auth/login` - вход
- `GET /api/auth/me` - текущий пользователь

### Billing
- `POST /api/billing/subscriptions` - создать подписку
- `POST /api/billing/limits/check` - проверить лимиты
- `POST /api/billing/usage` - записать использование

### Chat
- `POST /api/chat/conversations` - создать диалог
- `POST /api/chat/messages` - сохранить сообщение
- `GET /api/chat/conversations/{id}` - получить диалог с историей

## Следующие шаги

1. Middleware для авторизации (JWT проверка)
2. Интеграция с Python RAG сервисом
3. Реальная интеграция платежей (Stripe/YooKassa)
4. Тесты для каждого домена
