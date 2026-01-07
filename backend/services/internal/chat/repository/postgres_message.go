package repository

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"

	"github.com/google/uuid"
	"legalbot/services/internal/chat/domain"
)

type PostgresMessageRepository struct {
	db *sql.DB
}

func NewPostgresMessageRepository(db *sql.DB) *PostgresMessageRepository {
	return &PostgresMessageRepository{db: db}
}

func (r *PostgresMessageRepository) Create(ctx context.Context, msg *domain.Message) error {
	metadataJSON, _ := json.Marshal(msg.Metadata)
	query := `
		INSERT INTO messages (id, conversation_id, role, content, metadata, created_at)
		VALUES ($1, $2, $3, $4, $5, $6)
	`
	_, err := r.db.ExecContext(ctx, query,
		msg.ID, msg.ConversationID, msg.Role, msg.Content, string(metadataJSON), msg.CreatedAt)
	return err
}

func (r *PostgresMessageRepository) FindByConversationID(ctx context.Context, conversationID uuid.UUID) ([]*domain.Message, error) {
	query := `
		SELECT id, conversation_id, role, content, metadata, created_at
		FROM messages
		WHERE conversation_id = $1
		ORDER BY created_at ASC
	`
	rows, err := r.db.QueryContext(ctx, query, conversationID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var messages []*domain.Message
	for rows.Next() {
		msg := &domain.Message{}
		var metadataJSON string
		if err := rows.Scan(
			&msg.ID, &msg.ConversationID, &msg.Role, &msg.Content, &metadataJSON, &msg.CreatedAt,
		); err != nil {
			return nil, err
		}
		if err := json.Unmarshal([]byte(metadataJSON), &msg.Metadata); err != nil {
			msg.Metadata = make(map[string]interface{})
		}
		messages = append(messages, msg)
	}

	return messages, rows.Err()
}

func (r *PostgresMessageRepository) FindByID(ctx context.Context, id uuid.UUID) (*domain.Message, error) {
	query := `
		SELECT id, conversation_id, role, content, metadata, created_at
		FROM messages
		WHERE id = $1
	`
	msg := &domain.Message{}
	var metadataJSON string
	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&msg.ID, &msg.ConversationID, &msg.Role, &msg.Content, &metadataJSON, &msg.CreatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("message not found")
	}
	if err != nil {
		return nil, err
	}
	if err := json.Unmarshal([]byte(metadataJSON), &msg.Metadata); err != nil {
		msg.Metadata = make(map[string]interface{})
	}
	return msg, nil
}

func (r *PostgresMessageRepository) Delete(ctx context.Context, id uuid.UUID) error {
	query := `DELETE FROM messages WHERE id = $1`
	_, err := r.db.ExecContext(ctx, query, id)
	return err
}






