from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import analyze, answer, documents, ingest, report, search
from app.dependencies import close_dependencies, get_vector_repo, init_dependencies
from app.logging_setup import configure as configure_logging
from app.middleware import RequestContextMiddleware, register_exception_handlers

configure_logging(env=os.getenv("ENV", ""))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup_begin")
    await init_dependencies()
    logger.info("startup_ready")
    yield
    logger.info("shutdown")
    await close_dependencies()


app = FastAPI(
    title="LegalBot RAG API",
    version="2.0.0",
    description="Hybrid RAG service for Russian legal documents",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)
register_exception_handlers(app)

app.include_router(ingest.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(answer.router)
app.include_router(analyze.router)
app.include_router(report.router)


@app.get("/health", tags=["system"])
async def health():
    repo = get_vector_repo()
    stats = await repo.get_stats()
    return {"status": "ok", **stats}
