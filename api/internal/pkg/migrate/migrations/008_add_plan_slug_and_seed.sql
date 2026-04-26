-- +goose Up
ALTER TABLE plans ADD COLUMN IF NOT EXISTS slug VARCHAR(32) UNIQUE;

INSERT INTO plans (slug, name, price, max_requests, max_docs, features) VALUES
  ('free',       'Free',       0,      10,   5,    '["Basic support"]'),
  ('pro',        'Pro',        199000, 500,  100,  '["Priority support", "API access"]'),
  ('enterprise', 'Enterprise', 999000, 5000, 1000, '["Dedicated support", "SLA"]')
ON CONFLICT (slug) DO NOTHING;

-- +goose Down
DELETE FROM plans WHERE slug IN ('free','pro','enterprise');
ALTER TABLE plans DROP COLUMN IF EXISTS slug;
