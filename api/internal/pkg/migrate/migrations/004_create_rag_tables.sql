-- +goose Up
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS rag_documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id   TEXT NOT NULL UNIQUE,
    title       TEXT NOT NULL,
    doc_type    TEXT NOT NULL,
    year        INTEGER,
    meta        JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rag_chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(1024),
    meta        JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS rag_chunks_embedding_hnsw
    ON rag_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS rag_chunks_fts
    ON rag_chunks USING gin(to_tsvector('russian', content));

CREATE UNIQUE INDEX IF NOT EXISTS rag_chunks_doc_idx
    ON rag_chunks(document_id, chunk_index);

-- +goose Down
DROP TABLE IF EXISTS rag_chunks;
DROP TABLE IF EXISTS rag_documents;
DROP EXTENSION IF EXISTS vector;
