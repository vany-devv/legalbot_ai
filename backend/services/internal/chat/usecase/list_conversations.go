package usecase

import (
	"context"

	"github.com/google/uuid"
	"legalbot/services/internal/chat/domain"
)

type ListConversationsUseCase struct {
	conversationRepo domain.ConversationRepository
}

func NewListConversationsUseCase(conversationRepo domain.ConversationRepository) *ListConversationsUseCase {
	return &ListConversationsUseCase{conversationRepo: conversationRepo}
}

type ListConversationsResponse struct {
	ID        uuid.UUID `json:"id"`
	Title     string    `json:"title"`
	UpdatedAt string    `json:"updated_at"`
}

func (uc *ListConversationsUseCase) Execute(ctx context.Context, userID uuid.UUID, limit, offset int) ([]ListConversationsResponse, error) {
	if limit <= 0 {
		limit = 50
	}

	conversations, err := uc.conversationRepo.FindByUserID(ctx, userID, limit, offset)
	if err != nil {
		return nil, err
	}

	result := make([]ListConversationsResponse, 0, len(conversations))
	for _, c := range conversations {
		result = append(result, ListConversationsResponse{
			ID:        c.ID,
			Title:     c.Title,
			UpdatedAt: c.UpdatedAt.Format("2006-01-02T15:04:05Z"),
		})
	}

	return result, nil
}
