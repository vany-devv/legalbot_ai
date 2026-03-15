from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    source_id: str = Field(..., description="Unique document identifier, e.g. 'gk_rf'")
    title: str = Field(..., description="Human-readable title, e.g. 'Гражданский кодекс РФ'")
    doc_type: str = Field(..., description="Document type: kodeks | fz | postanovlenie | other")
    text: str = Field(..., description="Plain-text document content")
    year: int | None = None
    meta: dict = Field(default_factory=dict)


class IngestResponse(BaseModel):
    source_id: str
    chunks_added: int


class IngestJobResponse(BaseModel):
    job_id: str
    source_id: str
    status: str          # pending | running | done | failed
    progress: int = 0    # chunks embedded so far
    total: int = 0       # total chunks in document
    chunks_added: int = 0
    error: str | None = None


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=8, ge=1, le=50)


class CitationResponse(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    retrieval_score: float
    meta: dict


class SearchResponse(BaseModel):
    results: list[CitationResponse]


# ---------------------------------------------------------------------------
# Answer
# ---------------------------------------------------------------------------

class AnswerRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=8, ge=1, le=50)


class AnswerResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
