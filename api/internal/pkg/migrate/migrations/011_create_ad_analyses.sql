-- +goose Up
CREATE TABLE IF NOT EXISTS ad_analyses (
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    ad_text     TEXT NOT NULL,
    result      JSONB NOT NULL,
    citations   JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ad_analyses_user_created
    ON ad_analyses(user_id, created_at DESC);

-- +goose Down
DROP TABLE IF EXISTS ad_analyses;
