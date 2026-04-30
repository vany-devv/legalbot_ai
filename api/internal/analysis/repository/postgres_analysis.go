package repository

import (
	"context"
	"database/sql"
	"errors"
	"fmt"

	"github.com/google/uuid"
	"legalbot/services/internal/analysis/domain"
)

type PostgresAnalysisRepository struct {
	db *sql.DB
}

func NewPostgresAnalysisRepository(db *sql.DB) *PostgresAnalysisRepository {
	return &PostgresAnalysisRepository{db: db}
}

func (r *PostgresAnalysisRepository) Create(ctx context.Context, a *domain.AdAnalysis) error {
	const q = `
		INSERT INTO ad_analyses (id, user_id, title, ad_text, result, citations, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	_, err := r.db.ExecContext(ctx, q,
		a.ID, a.UserID, a.Title, a.AdText, []byte(a.Result), []byte(a.Citations), a.CreatedAt,
	)
	return err
}

func (r *PostgresAnalysisRepository) FindByID(ctx context.Context, id uuid.UUID) (*domain.AdAnalysis, error) {
	const q = `
		SELECT id, user_id, title, ad_text, result, citations, created_at
		FROM ad_analyses
		WHERE id = $1
	`
	var a domain.AdAnalysis
	var resultBytes, citationsBytes []byte
	err := r.db.QueryRowContext(ctx, q, id).Scan(
		&a.ID, &a.UserID, &a.Title, &a.AdText,
		&resultBytes, &citationsBytes, &a.CreatedAt,
	)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, fmt.Errorf("analysis not found")
	}
	if err != nil {
		return nil, err
	}
	a.Result = resultBytes
	a.Citations = citationsBytes
	return &a, nil
}

func (r *PostgresAnalysisRepository) List(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*domain.AdAnalysis, error) {
	const q = `
		SELECT id, user_id, title, ad_text, result, citations, created_at
		FROM ad_analyses
		WHERE user_id = $1
		ORDER BY created_at DESC
		LIMIT $2 OFFSET $3
	`
	rows, err := r.db.QueryContext(ctx, q, userID, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []*domain.AdAnalysis
	for rows.Next() {
		var a domain.AdAnalysis
		var resultBytes, citationsBytes []byte
		if err := rows.Scan(
			&a.ID, &a.UserID, &a.Title, &a.AdText,
			&resultBytes, &citationsBytes, &a.CreatedAt,
		); err != nil {
			return nil, err
		}
		a.Result = resultBytes
		a.Citations = citationsBytes
		out = append(out, &a)
	}
	return out, rows.Err()
}

func (r *PostgresAnalysisRepository) Delete(ctx context.Context, id, userID uuid.UUID) error {
	const q = `DELETE FROM ad_analyses WHERE id = $1 AND user_id = $2`
	res, err := r.db.ExecContext(ctx, q, id, userID)
	if err != nil {
		return err
	}
	n, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if n == 0 {
		return fmt.Errorf("analysis not found")
	}
	return nil
}
