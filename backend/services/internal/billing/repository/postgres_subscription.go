package repository

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/billing/domain"
)

type PostgresSubscriptionRepository struct {
	db *sql.DB
}

func NewPostgresSubscriptionRepository(db *sql.DB) *PostgresSubscriptionRepository {
	return &PostgresSubscriptionRepository{db: db}
}

func (r *PostgresSubscriptionRepository) Create(ctx context.Context, sub *domain.Subscription) error {
	query := `
		INSERT INTO subscriptions (id, user_id, plan_id, status, started_at, expires_at, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
	`
	_, err := r.db.ExecContext(ctx, query,
		sub.ID, sub.UserID, sub.PlanID, sub.Status, sub.StartedAt, sub.ExpiresAt, sub.CreatedAt, sub.UpdatedAt)
	return err
}

func (r *PostgresSubscriptionRepository) FindByUserID(ctx context.Context, userID uuid.UUID) (*domain.Subscription, error) {
	query := `
		SELECT id, user_id, plan_id, status, started_at, expires_at, created_at, updated_at
		FROM subscriptions
		WHERE user_id = $1
		ORDER BY created_at DESC
		LIMIT 1
	`
	sub := &domain.Subscription{}
	err := r.db.QueryRowContext(ctx, query, userID).Scan(
		&sub.ID, &sub.UserID, &sub.PlanID, &sub.Status, &sub.StartedAt, &sub.ExpiresAt, &sub.CreatedAt, &sub.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("subscription not found")
	}
	return sub, err
}

func (r *PostgresSubscriptionRepository) FindByID(ctx context.Context, id uuid.UUID) (*domain.Subscription, error) {
	query := `
		SELECT id, user_id, plan_id, status, started_at, expires_at, created_at, updated_at
		FROM subscriptions
		WHERE id = $1
	`
	sub := &domain.Subscription{}
	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&sub.ID, &sub.UserID, &sub.PlanID, &sub.Status, &sub.StartedAt, &sub.ExpiresAt, &sub.CreatedAt, &sub.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("subscription not found")
	}
	return sub, err
}

func (r *PostgresSubscriptionRepository) Update(ctx context.Context, sub *domain.Subscription) error {
	sub.UpdatedAt = time.Now()
	query := `
		UPDATE subscriptions
		SET plan_id = $2, status = $3, expires_at = $4, updated_at = $5
		WHERE id = $1
	`
	_, err := r.db.ExecContext(ctx, query, sub.ID, sub.PlanID, sub.Status, sub.ExpiresAt, sub.UpdatedAt)
	return err
}

func (r *PostgresSubscriptionRepository) Cancel(ctx context.Context, id uuid.UUID) error {
	query := `UPDATE subscriptions SET status = 'cancelled', updated_at = NOW() WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}






