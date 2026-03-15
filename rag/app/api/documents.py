from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_vector_repo, verify_ingest_key
from app.storage.pgvector import VectorRepository

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
async def list_documents(
    repo: VectorRepository = Depends(get_vector_repo),
) -> list[dict]:
    return await repo.list_documents()


@router.delete("/{source_id}", dependencies=[Depends(verify_ingest_key)])
async def delete_document(
    source_id: str,
    repo: VectorRepository = Depends(get_vector_repo),
) -> dict:
    deleted = await repo.delete_document(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": source_id}
