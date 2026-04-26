package repository

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"

	"github.com/google/uuid"
	"legalbot/services/internal/billing/domain"
)

type PostgresPlanRepository struct {
	db *sql.DB
}

func NewPostgresPlanRepository(db *sql.DB) *PostgresPlanRepository {
	return &PostgresPlanRepository{db: db}
}

func (r *PostgresPlanRepository) scanPlan(row interface {
	Scan(dest ...any) error
}) (*domain.Plan, error) {
	plan := &domain.Plan{}
	var slug sql.NullString
	var featuresJSON string
	if err := row.Scan(
		&plan.ID, &slug, &plan.Name, &plan.Price, &plan.MaxRequests, &plan.MaxDocs, &featuresJSON, &plan.CreatedAt,
	); err != nil {
		return nil, err
	}
	if slug.Valid {
		plan.Slug = slug.String
	}
	if err := json.Unmarshal([]byte(featuresJSON), &plan.Features); err != nil {
		return nil, fmt.Errorf("failed to parse features: %w", err)
	}
	return plan, nil
}

func (r *PostgresPlanRepository) FindByID(ctx context.Context, id uuid.UUID) (*domain.Plan, error) {
	query := `
		SELECT id, slug, name, price, max_requests, max_docs, features, created_at
		FROM plans
		WHERE id = $1
	`
	plan, err := r.scanPlan(r.db.QueryRowContext(ctx, query, id))
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("plan not found")
	}
	return plan, err
}

func (r *PostgresPlanRepository) FindBySlug(ctx context.Context, slug string) (*domain.Plan, error) {
	query := `
		SELECT id, slug, name, price, max_requests, max_docs, features, created_at
		FROM plans
		WHERE slug = $1
	`
	plan, err := r.scanPlan(r.db.QueryRowContext(ctx, query, slug))
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("plan not found")
	}
	return plan, err
}

func (r *PostgresPlanRepository) FindAll(ctx context.Context) ([]*domain.Plan, error) {
	query := `
		SELECT id, slug, name, price, max_requests, max_docs, features, created_at
		FROM plans
		ORDER BY price ASC
	`
	rows, err := r.db.QueryContext(ctx, query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var plans []*domain.Plan
	for rows.Next() {
		plan, err := r.scanPlan(rows)
		if err != nil {
			return nil, err
		}
		plans = append(plans, plan)
	}

	return plans, rows.Err()
}
