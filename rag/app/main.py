from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, answer, documents, ingest, search
from app.dependencies import close_dependencies, get_vector_repo, init_dependencies

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising DB pool and embedder...")
    await init_dependencies()
    logger.info("Ready.")
    yield
    logger.info("Shutting down...")
    await close_dependencies()


app = FastAPI(
    title="LegalBot RAG API",
    version="2.0.0",
    description="Hybrid RAG service for Russian legal documents",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(answer.router)
app.include_router(analyze.router)


@app.get("/health", tags=["system"])
async def health():
    repo = get_vector_repo()
    stats = await repo.get_stats()
    return {"status": "ok", **stats}
