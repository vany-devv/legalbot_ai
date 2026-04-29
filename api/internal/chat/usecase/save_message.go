package usecase

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/chat/domain"
)

type SaveMessageUseCase struct {
	conversationRepo domain.ConversationRepository
	messageRepo      domain.MessageRepository
	citationRepo     domain.CitationRepository
}

func NewSaveMessageUseCase(
	conversationRepo domain.ConversationRepository,
	messageRepo domain.MessageRepository,
	citationRepo domain.CitationRepository,
) *SaveMessageUseCase {
	return &SaveMessageUseCase{
		conversationRepo: conversationRepo,
		messageRepo:      messageRepo,
		citationRepo:     citationRepo,
	}
}

type SaveMessageRequest struct {
	UserID         uuid.UUID
	ConversationID uuid.UUID
	Role           string
	Content        string
	Metadata       map[string]interface{}
	Citations      []CitationData
}

type SaveMessageResponse struct {
	MessageID uuid.UUID
	CreatedAt time.Time
}

func (uc *SaveMessageUseCase) Execute(ctx context.Context, req SaveMessageRequest) (*SaveMessageResponse, error) {
	if req.UserID == uuid.Nil {
		return nil, errors.New("user id is required")
	}

	conversation, err := uc.conversationRepo.FindByID(ctx, req.ConversationID)
	if err != nil {
		return nil, ErrConversationNotFound
	}
	if conversation.UserID != req.UserID {
		return nil, ErrConversationForbidden
	}

	message := &domain.Message{
		ID:             uuid.New(),
		ConversationID: req.ConversationID,
		Role:           req.Role,
		Content:        req.Content,
		Metadata:       req.Metadata,
		CreatedAt:      time.Now(),
	}

	if err := uc.messageRepo.Create(ctx, message); err != nil {
		return nil, fmt.Errorf("failed to create message: %w", err)
	}

	for _, citData := range req.Citations {
		citation := &domain.Citation{
			ID:        uuid.New(),
			MessageID: message.ID,
			ChunkID:   citData.ChunkID,
			SourceID:  citData.SourceID,
			Score:     citData.Score,
			Quote:     citData.Quote,
			Meta:      citData.Meta,
			CreatedAt: time.Now(),
		}
		uc.citationRepo.Create(ctx, citation)
	}

	return &SaveMessageResponse{
		MessageID: message.ID,
		CreatedAt: message.CreatedAt,
	}, nil
}
