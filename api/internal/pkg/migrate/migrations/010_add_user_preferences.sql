-- +goose Up
-- Add user preferences (independent palette + future-proof prefs blob)
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS preferred_palette VARCHAR(32) NOT NULL DEFAULT 'navy';

-- Backfill: existing rows already get 'navy' via DEFAULT. No-op insert.

-- +goose Down
ALTER TABLE users DROP COLUMN IF EXISTS preferred_palette;
