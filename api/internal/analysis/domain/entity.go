package domain

import (
	"context"
	"encoding/json"
	"time"

	"github.com/google/uuid"
)

// AdAnalysis — сохранённый анализ рекламного материала.
// Result и Citations хранятся как сырая JSON-payload — формат полностью повторяет
// SSE-события из RAG, чтобы фронт мог рендерить так же, как в реальном времени.
type AdAnalysis struct {
	ID        uuid.UUID
	UserID    uuid.UUID
	Title     string
	AdText    string
	Result    json.RawMessage
	Citations json.RawMessage
	CreatedAt time.Time
}

type AdAnalysisRepository interface {
	Create(ctx context.Context, a *AdAnalysis) error
	FindByID(ctx context.Context, id uuid.UUID) (*AdAnalysis, error)
	List(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*AdAnalysis, error)
	Delete(ctx context.Context, id, userID uuid.UUID) error
}
