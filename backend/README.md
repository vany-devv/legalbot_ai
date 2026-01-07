# LegalBot Backend (Poetry)

## Установка

```bash
cd backend
poetry install --no-root
```

## Запуск сервера

```bash
# переменные окружения (опционально)
export PORT=8000
# export OPENAI_API_KEY=...

# активация окружения Poetry
poetry run python app/main.py
# или через uvicorn
# poetry run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Тестовые данные

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d @backend/samples/docs.json
```


