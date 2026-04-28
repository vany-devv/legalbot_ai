package repository

import (
	"context"
	"database/sql"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/billing/domain"
)

type PostgresUsageRepository struct {
	db *sql.DB
}

func NewPostgresUsageRepository(db *sql.DB) *PostgresUsageRepository {
	return &PostgresUsageRepository{db: db}
}

func (r *PostgresUsageRepository) Create(ctx context.Context, usage *domain.Usage) error {
	query := `
		INSERT INTO usage (id, user_id, resource_type, count, period_start, period_end, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	_, err := r.db.ExecContext(ctx, query,
		usage.ID, usage.UserID, usage.ResourceType, usage.Count, usage.PeriodStart, usage.PeriodEnd, usage.CreatedAt)
	return err
}

func (r *PostgresUsageRepository) GetByUserAndPeriod(ctx context.Context, userID uuid.UUID, resourceType string, start, end time.Time) (*domain.Usage, error) {
	// Increment пишет period как [date_trunc('month', NOW()), +1 month).
	// Старая проверка `period_start >= start AND period_end <= end` со start = NOW()-1mo, end = NOW()
	// никогда не сходилась (period_end всегда в будущем) → метод молча возвращал nil.
	// Ищем запись, чей полуинтервал покрывает момент `end` — это и есть текущий период.
	query := `
		SELECT id, user_id, resource_type, count, period_start, period_end, created_at
		FROM usage
		WHERE user_id = $1 AND resource_type = $2
		  AND period_start <= $3 AND period_end > $3
		ORDER BY created_at DESC
		LIMIT 1
	`
	usage := &domain.Usage{}
	err := r.db.QueryRowContext(ctx, query, userID, resourceType, end).Scan(
		&usage.ID, &usage.UserID, &usage.ResourceType, &usage.Count, &usage.PeriodStart, &usage.PeriodEnd, &usage.CreatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	_ = start // параметр оставлен для совместимости интерфейса
	return usage, err
}

func (r *PostgresUsageRepository) Increment(ctx context.Context, userID uuid.UUID, resourceType string, count int) error {
	// Используем UPSERT для инкремента
	query := `
		INSERT INTO usage (id, user_id, resource_type, count, period_start, period_end, created_at)
		VALUES (gen_random_uuid(), $1, $2, $3, date_trunc('month', NOW()), date_trunc('month', NOW()) + interval '1 month', NOW())
		ON CONFLICT (user_id, resource_type, period_start)
		DO UPDATE SET count = usage.count + $3
	`
	_, err := r.db.ExecContext(ctx, query, userID, resourceType, count)
	return err
}






