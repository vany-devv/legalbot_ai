from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from io import BytesIO

import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.api.schemas import IngestJobResponse, IngestRequest, IngestResponse
from app.config import settings
from app.core.chunking import LegalDocumentChunker, SimpleChunker
from app.core.embeddings import BaseEmbedder
from app.dependencies import get_embedder, get_vector_repo, verify_ingest_key
from app.storage.pgvector import ChunkData, VectorRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])


# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------

@dataclass
class _Job:
    job_id: str
    source_id: str
    status: str = "pending"   # pending | running | done | failed
    progress: int = 0
    total: int = 0
    chunks_added: int = 0
    error: str | None = None


_jobs: dict[str, _Job] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_mhtml(content: bytes) -> str:
    """Extract plain text from MHTML (web archive) files.

    pravo.gov.ru serves legal documents as MHTML with a .rtf extension.
    """
    import email
    import html
    import re as _re

    msg = email.message_from_bytes(content)

    html_content: str | None = None
    for part in (msg.walk() if msg.is_multipart() else [msg]):
        ct = part.get_content_type() or ""
        if "html" not in ct:
            continue
        charset = part.get_content_charset() or "cp1251"
        payload = part.get_payload(decode=True)
        if payload:
            html_content = payload.decode(charset, errors="replace")
            break

    if not html_content:
        return content.decode("cp1251", errors="replace")

    # Strip <head>, <style>, <script> blocks entirely (content + tags)
    html_content = _re.sub(r"<head\b[^>]*>.*?</head>", "", html_content, flags=_re.IGNORECASE | _re.DOTALL)
    html_content = _re.sub(r"<style\b[^>]*>.*?</style>", "", html_content, flags=_re.IGNORECASE | _re.DOTALL)
    html_content = _re.sub(r"<script\b[^>]*>.*?</script>", "", html_content, flags=_re.IGNORECASE | _re.DOTALL)
    # Convert block-level elements to newlines before stripping tags
    html_content = _re.sub(r"<br\s*/?>", "\n", html_content, flags=_re.IGNORECASE)
    html_content = _re.sub(r"</?(?:p|div|tr|li)[^>]*>", "\n", html_content, flags=_re.IGNORECASE)
    html_content = _re.sub(r"<[^>]+>", "", html_content)
    return html.unescape(html_content)


def _extract_text(content: bytes, filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        import fitz

        doc = fitz.open(stream=content, filetype="pdf")
        return "\n\n".join(page.get_text() for page in doc)
    if name.endswith(".docx"):
        from docx import Document

        doc = Document(BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    if name.endswith(".rtf"):
        import re as _re

        # pravo.gov.ru sends MHTML (web archive) files with a .rtf extension
        if content.lstrip()[:12].startswith(b"MIME-Version"):
            return _extract_mhtml(content)

        import html
        from striprtf.striprtf import rtf_to_text

        cp_match = _re.search(rb"\\ansicpg(\d+)", content[:500])
        encoding = f"cp{cp_match.group(1).decode()}" if cp_match else "cp1251"
        try:
            rtf_str = content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            rtf_str = content.decode("utf-8", errors="replace")

        text = rtf_to_text(rtf_str)
        text = _re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        return text
    return content.decode("utf-8", errors="replace")


def _pick_chunker(doc_type: str, law_name: str):
    if doc_type in ("kodeks", "fz", "postanovlenie"):
        return LegalDocumentChunker(
            law_name=law_name,
            max_len=settings.chunk_max_len,
            overlap=settings.chunk_overlap,
        )
    return SimpleChunker(max_len=settings.chunk_max_len, overlap=settings.chunk_overlap)


# ---------------------------------------------------------------------------
# Background job runner
# ---------------------------------------------------------------------------

async def _run_ingest_job(
    job_id: str,
    source_id: str,
    title: str,
    doc_type: str,
    text: str,
    year: int | None,
    meta: dict,
    repo: VectorRepository,
    embedder: BaseEmbedder,
) -> None:
    job = _jobs[job_id]
    job.status = "running"
    try:
        chunker = _pick_chunker(doc_type, title)
        raw_chunks = chunker.split(text)

        if not raw_chunks:
            raise ValueError("Document produced zero chunks")

        job.total = len(raw_chunks)
        logger.info("Job %s: embedding %d chunks for '%s'", job_id, job.total, source_id)

        # Embed one by one to track progress (also respects rate limits naturally)
        embeddings: list[np.ndarray] = []
        for chunk in raw_chunks:
            emb = await embedder.embed_documents([chunk.content])
            embeddings.append(emb[0])
            job.progress += 1

        doc_id = await repo.add_document(
            source_id=source_id,
            title=title,
            doc_type=doc_type,
            year=year,
            meta=meta,
        )
        chunk_data = [
            ChunkData(
                index=c.index,
                content=c.content,
                embedding=embeddings[i],
                meta=c.meta,
            )
            for i, c in enumerate(raw_chunks)
        ]
        job.chunks_added = await repo.add_chunks(doc_id, chunk_data)
        job.status = "done"
        logger.info("Job %s: done — %d chunks added", job_id, job.chunks_added)

    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        logger.exception("Job %s failed: %s", job_id, exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def _job_to_response(j: _Job) -> IngestJobResponse:
    return IngestJobResponse(
        job_id=j.job_id,
        source_id=j.source_id,
        status=j.status,
        progress=j.progress,
        total=j.total,
        chunks_added=j.chunks_added,
        error=j.error,
    )


@router.post("/upload", response_model=IngestJobResponse,
             dependencies=[Depends(verify_ingest_key)])
async def ingest_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_id: str = Form(...),
    title: str = Form(...),
    doc_type: str = Form("other"),
    year: int | None = Form(default=None),
    repo: VectorRepository = Depends(get_vector_repo),
    embedder: BaseEmbedder = Depends(get_embedder),
) -> IngestJobResponse:
    content = await file.read()
    text = _extract_text(content, file.filename or "upload.txt")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = _Job(job_id=job_id, source_id=source_id)

    background_tasks.add_task(
        _run_ingest_job,
        job_id, source_id, title, doc_type, text, year, {}, repo, embedder,
    )

    logger.info("Job %s created for '%s'", job_id, source_id)
    return _job_to_response(_jobs[job_id])


@router.get("/jobs/{job_id}", response_model=IngestJobResponse)
async def get_job_status(job_id: str) -> IngestJobResponse:
    """Poll ingest job status. No auth required — job_id UUID is unguessable."""
    j = _jobs.get(job_id)
    if j is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(j)


@router.post("", response_model=IngestResponse, dependencies=[Depends(verify_ingest_key)])
async def ingest_json(
    req: IngestRequest,
    repo: VectorRepository = Depends(get_vector_repo),
    embedder: BaseEmbedder = Depends(get_embedder),
) -> IngestResponse:
    """Synchronous JSON ingest — use only for small documents."""
    chunker = _pick_chunker(req.doc_type, req.title)
    raw_chunks = chunker.split(req.text)
    if not raw_chunks:
        raise HTTPException(status_code=422, detail="Document produced zero chunks")

    texts = [c.content for c in raw_chunks]
    embeddings = await embedder.embed_documents(texts)

    doc_id = await repo.add_document(
        source_id=req.source_id,
        title=req.title,
        doc_type=req.doc_type,
        year=req.year,
        meta=req.meta,
    )
    chunk_data = [
        ChunkData(index=c.index, content=c.content, embedding=embeddings[i], meta=c.meta)
        for i, c in enumerate(raw_chunks)
    ]
    added = await repo.add_chunks(doc_id, chunk_data)
    return IngestResponse(source_id=req.source_id, chunks_added=added)
