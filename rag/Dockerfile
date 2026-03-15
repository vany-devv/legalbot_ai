# Build stage — compile C extensions and install deps
FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "fastapi>=0.121.0,<0.122.0" \
    "uvicorn[standard]>=0.38.0,<0.39.0" \
    "numpy>=2.0.0,<3.0.0" \
    "pydantic>=2.12.4,<3.0.0" \
    "pydantic-settings>=2.9.0,<3.0.0" \
    "openai>=1.0.0,<3.0.0" \
    "asyncpg>=0.30.0,<1.0.0" \
    "pgvector>=0.3.6,<1.0.0" \
    "pymupdf>=1.26.0,<2.0.0" \
    "sse-starlette>=2.3.0,<3.0.0" \
    "tenacity>=9.1.0,<10.0.0" \
    "httpx>=0.28.0,<1.0.0" \
    "python-docx>=1.1.0,<1.2.0" \
    "python-multipart>=0.0.9,<0.1.0" \
    "striprtf>=0.0.28"

# Runtime stage — no build tools, smaller final image
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
