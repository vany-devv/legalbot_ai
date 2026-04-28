-- +goose Up
ALTER TABLE subscriptions ALTER COLUMN expires_at DROP NOT NULL;

INSERT INTO subscriptions (user_id, plan_id, status, started_at, expires_at)
SELECT u.id, (SELECT id FROM plans WHERE slug = 'free'), 'active', NOW(), NULL
FROM users u
WHERE NOT EXISTS (SELECT 1 FROM subscriptions s WHERE s.user_id = u.id);

-- +goose Down
ALTER TABLE subscriptions ALTER COLUMN expires_at SET NOT NULL;
