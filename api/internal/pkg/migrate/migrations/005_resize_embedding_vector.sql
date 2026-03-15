-- +goose Up
-- Resize embedding column from 1024 to 256 dims (Yandex Cloud embeddings)
-- Existing embeddings are dropped since they were produced by a different model
DROP INDEX IF EXISTS rag_chunks_embedding_hnsw;

ALTER TABLE rag_chunks DROP COLUMN IF EXISTS embedding;
ALTER TABLE rag_chunks ADD COLUMN embedding vector(256);

CREATE INDEX IF NOT EXISTS rag_chunks_embedding_hnsw
    ON rag_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- +goose Down
DROP INDEX IF EXISTS rag_chunks_embedding_hnsw;

ALTER TABLE rag_chunks DROP COLUMN IF EXISTS embedding;
ALTER TABLE rag_chunks ADD COLUMN embedding vector(1024);

CREATE INDEX IF NOT EXISTS rag_chunks_embedding_hnsw
    ON rag_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
