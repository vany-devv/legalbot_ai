package usecase

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/google/uuid"
	"legalbot/services/internal/analysis/domain"
)

var ErrForbidden = errors.New("analysis: access forbidden")

const (
	maxTitleChars = 60
	listMaxLimit  = 100
)

// ─── Save ────────────────────────────────────────────────────────────

type SaveRequest struct {
	UserID    uuid.UUID
	AdText    string
	Result    json.RawMessage
	Citations json.RawMessage
}

type SaveAnalysisUseCase struct {
	repo domain.AdAnalysisRepository
}

func NewSaveAnalysisUseCase(repo domain.AdAnalysisRepository) *SaveAnalysisUseCase {
	return &SaveAnalysisUseCase{repo: repo}
}

func (uc *SaveAnalysisUseCase) Execute(ctx context.Context, req SaveRequest) (*domain.AdAnalysis, error) {
	if len(req.Result) == 0 {
		req.Result = json.RawMessage(`{}`)
	}
	if len(req.Citations) == 0 {
		req.Citations = json.RawMessage(`[]`)
	}

	a := &domain.AdAnalysis{
		ID:        uuid.New(),
		UserID:    req.UserID,
		Title:     deriveTitle(req.AdText),
		AdText:    req.AdText,
		Result:    req.Result,
		Citations: req.Citations,
		CreatedAt: time.Now().UTC(),
	}
	if err := uc.repo.Create(ctx, a); err != nil {
		return nil, err
	}
	return a, nil
}

// deriveTitle: первая «осмысленная» фраза из материала — до точки или до 60 символов,
// обрезается по границе слова. Если материал пустой — fallback с датой.
func deriveTitle(adText string) string {
	cleaned := strings.TrimSpace(adText)
	if cleaned == "" {
		return "Анализ от " + time.Now().Format("02.01.2006 15:04")
	}
	cleaned = strings.ReplaceAll(cleaned, "\n", " ")
	cleaned = strings.Join(strings.Fields(cleaned), " ")

	if i := strings.IndexAny(cleaned, ".!?"); i > 0 && i < maxTitleChars {
		return cleaned[:i]
	}
	if utf8.RuneCountInString(cleaned) <= maxTitleChars {
		return cleaned
	}
	// truncate by rune
	runes := []rune(cleaned)
	cut := runes[:maxTitleChars]
	// rollback to last space to avoid mid-word
	for i := len(cut) - 1; i > maxTitleChars/2; i-- {
		if cut[i] == ' ' {
			return strings.TrimSpace(string(cut[:i])) + "…"
		}
	}
	return strings.TrimSpace(string(cut)) + "…"
}

// ─── List ────────────────────────────────────────────────────────────

type ListItem struct {
	ID        uuid.UUID `json:"id"`
	Title     string    `json:"title"`
	CreatedAt time.Time `json:"created_at"`
}

type ListAnalysesUseCase struct {
	repo domain.AdAnalysisRepository
}

func NewListAnalysesUseCase(repo domain.AdAnalysisRepository) *ListAnalysesUseCase {
	return &ListAnalysesUseCase{repo: repo}
}

func (uc *ListAnalysesUseCase) Execute(ctx context.Context, userID uuid.UUID, limit, offset int) ([]ListItem, error) {
	if limit <= 0 || limit > listMaxLimit {
		limit = 50
	}
	if offset < 0 {
		offset = 0
	}
	items, err := uc.repo.List(ctx, userID, limit, offset)
	if err != nil {
		return nil, err
	}
	out := make([]ListItem, 0, len(items))
	for _, a := range items {
		out = append(out, ListItem{
			ID:        a.ID,
			Title:     a.Title,
			CreatedAt: a.CreatedAt,
		})
	}
	return out, nil
}

// ─── Get ─────────────────────────────────────────────────────────────

type GetResponse struct {
	ID        uuid.UUID       `json:"id"`
	Title     string          `json:"title"`
	AdText    string          `json:"ad_text"`
	Result    json.RawMessage `json:"result"`
	Citations json.RawMessage `json:"citations"`
	CreatedAt time.Time       `json:"created_at"`
}

type GetAnalysisUseCase struct {
	repo domain.AdAnalysisRepository
}

func NewGetAnalysisUseCase(repo domain.AdAnalysisRepository) *GetAnalysisUseCase {
	return &GetAnalysisUseCase{repo: repo}
}

func (uc *GetAnalysisUseCase) Execute(ctx context.Context, id, userID uuid.UUID) (*GetResponse, error) {
	a, err := uc.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if a.UserID != userID {
		return nil, ErrForbidden
	}
	return &GetResponse{
		ID:        a.ID,
		Title:     a.Title,
		AdText:    a.AdText,
		Result:    a.Result,
		Citations: a.Citations,
		CreatedAt: a.CreatedAt,
	}, nil
}

// ─── Delete ──────────────────────────────────────────────────────────

type DeleteAnalysisUseCase struct {
	repo domain.AdAnalysisRepository
}

func NewDeleteAnalysisUseCase(repo domain.AdAnalysisRepository) *DeleteAnalysisUseCase {
	return &DeleteAnalysisUseCase{repo: repo}
}

func (uc *DeleteAnalysisUseCase) Execute(ctx context.Context, id, userID uuid.UUID) error {
	return uc.repo.Delete(ctx, id, userID)
}
