# Frontend — Nuxt 3

Веб-интерфейс для LegalBot AI. Стриминг ответов, история диалогов, управление базой знаний.

## Стек

- **Nuxt 3** + Vue 3 Composition API
- **Tailwind CSS** с CSS-переменными для тем
- **marked** для рендеринга markdown ответов
- SSE (Server-Sent Events) для стриминга через ReadableStream API

## Конфигурация

Переменные задаются в `nuxt.config.ts` или через env:

| Переменная | Описание |
|-----------|---------|
| `API_URL` | URL Go API (server-side, для SSR) |
| `NUXT_PUBLIC_API_BASE` | URL API (client-side) |

В dev-режиме запросы проксируются через Nuxt Nitro, поэтому CORS не нужен.

## Локальная разработка

```bash
cd frontend
npm install
npm run dev
```

Приложение стартует на `http://localhost:3000`. Proxy к API (`/api/*`) настроен в `nuxt.config.ts`.

## Сборка

```bash
npm run build
node .output/server/index.mjs
```

## Структура

```
pages/
  index.vue          — главная страница чата
  chat/[id].vue      — конкретный диалог
  admin.vue          — управление базой знаний
  auth/              — логин и регистрация
components/
  ChatSidebar.vue    — боковая панель с историей
  ChatMessage.vue    — рендер сообщения (markdown + цитаты)
  ChatInput.vue      — поле ввода с авторесайзом
  CitationCard.vue   — карточка источника
  ThinkingBlock.vue  — блок "размышлений" AI
composables/
  useChat.ts         — стейт диалогов, SSE стриминг
  useAuth.ts         — JWT авторизация
  useTheme.ts        — тёмная/светлая тема
  useSidebar.ts      — состояние сайдбара
```
