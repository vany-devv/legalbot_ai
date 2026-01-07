package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/chat/domain"
)

type CreateConversationUseCase struct {
	conversationRepo domain.ConversationRepository
}

func NewCreateConversationUseCase(conversationRepo domain.ConversationRepository) *CreateConversationUseCase {
	return &CreateConversationUseCase{conversationRepo: conversationRepo}
}

type CreateConversationRequest struct {
	UserID uuid.UUID
	Title  string
}

type CreateConversationResponse struct {
	ConversationID uuid.UUID
	Title           string
	CreatedAt       time.Time
}

func (uc *CreateConversationUseCase) Execute(ctx context.Context, req CreateConversationRequest) (*CreateConversationResponse, error) {
	title := req.Title
	if title == "" {
		title = "New Conversation"
	}

	conversation := &domain.Conversation{
		ID:        uuid.New(),
		UserID:    req.UserID,
		Title:     title,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	if err := uc.conversationRepo.Create(ctx, conversation); err != nil {
		return nil, fmt.Errorf("failed to create conversation: %w", err)
	}

	return &CreateConversationResponse{
		ConversationID: conversation.ID,
		Title:           conversation.Title,
		CreatedAt:       conversation.CreatedAt,
	}, nil
}






