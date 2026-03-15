package repository

import (
	"context"
	"database/sql"
	"encoding/json"

	"github.com/google/uuid"
	"legalbot/services/internal/chat/domain"
)

type PostgresCitationRepository struct {
	db *sql.DB
}

func NewPostgresCitationRepository(db *sql.DB) *PostgresCitationRepository {
	return &PostgresCitationRepository{db: db}
}

func (r *PostgresCitationRepository) Create(ctx context.Context, citation *domain.Citation) error {
	metaJSON, _ := json.Marshal(citation.Meta)
	query := `
		INSERT INTO citations (id, message_id, chunk_id, source_id, score, quote, meta, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
	`
	_, err := r.db.ExecContext(ctx, query,
		citation.ID, citation.MessageID, citation.ChunkID, citation.SourceID,
		citation.Score, citation.Quote, string(metaJSON), citation.CreatedAt)
	return err
}

func (r *PostgresCitationRepository) FindByMessageID(ctx context.Context, messageID uuid.UUID) ([]*domain.Citation, error) {
	query := `
		SELECT id, message_id, chunk_id, source_id, score, quote, meta, created_at
		FROM citations
		WHERE message_id = $1
		ORDER BY score DESC
	`
	rows, err := r.db.QueryContext(ctx, query, messageID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var citations []*domain.Citation
	for rows.Next() {
		cit := &domain.Citation{}
		var metaJSON string
		if err := rows.Scan(
			&cit.ID, &cit.MessageID, &cit.ChunkID, &cit.SourceID,
			&cit.Score, &cit.Quote, &metaJSON, &cit.CreatedAt,
		); err != nil {
			return nil, err
		}
		if err := json.Unmarshal([]byte(metaJSON), &cit.Meta); err != nil {
			cit.Meta = make(map[string]interface{})
		}
		citations = append(citations, cit)
	}

	return citations, rows.Err()
}

func (r *PostgresCitationRepository) DeleteByMessageID(ctx context.Context, messageID uuid.UUID) error {
	query := `DELETE FROM citations WHERE message_id = $1`
	_, err := r.db.ExecContext(ctx, query, messageID)
	return err
}






