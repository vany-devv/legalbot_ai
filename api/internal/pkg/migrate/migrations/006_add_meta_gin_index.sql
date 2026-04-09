-- +goose Up
CREATE INDEX IF NOT EXISTS rag_chunks_meta_gin ON rag_chunks USING gin(meta);

-- +goose Down
DROP INDEX IF EXISTS rag_chunks_meta_gin;
