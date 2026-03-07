package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/chat/domain"
)

type SaveMessageUseCase struct {
	messageRepo  domain.MessageRepository
	citationRepo domain.CitationRepository
}

func NewSaveMessageUseCase(
	messageRepo domain.MessageRepository,
	citationRepo domain.CitationRepository,
) *SaveMessageUseCase {
	return &SaveMessageUseCase{
		messageRepo:  messageRepo,
		citationRepo: citationRepo,
	}
}

type SaveMessageRequest struct {
	ConversationID uuid.UUID
	Role           string // user, assistant
	Content        string
	Metadata       map[string]interface{} // provider, model, confidence
	Citations      []CitationData
}

type SaveMessageResponse struct {
	MessageID uuid.UUID
	CreatedAt time.Time
}

func (uc *SaveMessageUseCase) Execute(ctx context.Context, req SaveMessageRequest) (*SaveMessageResponse, error) {
	// Создание сообщения
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

	// Сохранение цитат (если есть)
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

		if err := uc.citationRepo.Create(ctx, citation); err != nil {
			// Логируем ошибку, но не прерываем сохранение сообщения
			// TODO: добавить логирование
			continue
		}
	}

	return &SaveMessageResponse{
		MessageID: message.ID,
		CreatedAt: message.CreatedAt,
	}, nil
}






