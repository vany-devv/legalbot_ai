package repository

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/chat/domain"
)

type PostgresConversationRepository struct {
	db *sql.DB
}

func NewPostgresConversationRepository(db *sql.DB) *PostgresConversationRepository {
	return &PostgresConversationRepository{db: db}
}

func (r *PostgresConversationRepository) Create(ctx context.Context, conv *domain.Conversation) error {
	query := `
		INSERT INTO conversations (id, user_id, title, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5)
	`
	_, err := r.db.ExecContext(ctx, query, conv.ID, conv.UserID, conv.Title, conv.CreatedAt, conv.UpdatedAt)
	return err
}

func (r *PostgresConversationRepository) FindByID(ctx context.Context, id uuid.UUID) (*domain.Conversation, error) {
	query := `
		SELECT id, user_id, title, created_at, updated_at
		FROM conversations
		WHERE id = $1
	`
	conv := &domain.Conversation{}
	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&conv.ID, &conv.UserID, &conv.Title, &conv.CreatedAt, &conv.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("conversation not found")
	}
	return conv, err
}

func (r *PostgresConversationRepository) FindByUserID(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*domain.Conversation, error) {
	query := `
		SELECT id, user_id, title, created_at, updated_at
		FROM conversations
		WHERE user_id = $1
		ORDER BY updated_at DESC
		LIMIT $2 OFFSET $3
	`
	rows, err := r.db.QueryContext(ctx, query, userID, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var conversations []*domain.Conversation
	for rows.Next() {
		conv := &domain.Conversation{}
		if err := rows.Scan(
			&conv.ID, &conv.UserID, &conv.Title, &conv.CreatedAt, &conv.UpdatedAt,
		); err != nil {
			return nil, err
		}
		conversations = append(conversations, conv)
	}

	return conversations, rows.Err()
}

func (r *PostgresConversationRepository) Update(ctx context.Context, conv *domain.Conversation) error {
	conv.UpdatedAt = time.Now()
	query := `
		UPDATE conversations
		SET title = $2, updated_at = $3
		WHERE id = $1
	`
	_, err := r.db.ExecContext(ctx, query, conv.ID, conv.Title, conv.UpdatedAt)
	return err
}

func (r *PostgresConversationRepository) Delete(ctx context.Context, id uuid.UUID) error {
	query := `DELETE FROM conversations WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}






