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

func (r *PostgresPlanRepository) FindByID(ctx context.Context, id uuid.UUID) (*domain.Plan, error) {
	query := `
		SELECT id, name, price, max_requests, max_docs, features, created_at
		FROM plans
		WHERE id = $1
	`
	plan := &domain.Plan{}
	var featuresJSON string
	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&plan.ID, &plan.Name, &plan.Price, &plan.MaxRequests, &plan.MaxDocs, &featuresJSON, &plan.CreatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("plan not found")
	}
	if err != nil {
		return nil, err
	}

	// Парсинг features из JSON
	if err := json.Unmarshal([]byte(featuresJSON), &plan.Features); err != nil {
		return nil, fmt.Errorf("failed to parse features: %w", err)
	}

	return plan, nil
}

func (r *PostgresPlanRepository) FindAll(ctx context.Context) ([]*domain.Plan, error) {
	query := `
		SELECT id, name, price, max_requests, max_docs, features, created_at
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
		plan := &domain.Plan{}
		var featuresJSON string
		if err := rows.Scan(
			&plan.ID, &plan.Name, &plan.Price, &plan.MaxRequests, &plan.MaxDocs, &featuresJSON, &plan.CreatedAt,
		); err != nil {
			return nil, err
		}
		if err := json.Unmarshal([]byte(featuresJSON), &plan.Features); err != nil {
			return nil, fmt.Errorf("failed to parse features: %w", err)
		}
		plans = append(plans, plan)
	}

	return plans, rows.Err()
}






