package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/chat/domain"
)

type GetConversationUseCase struct {
	conversationRepo domain.ConversationRepository
	messageRepo      domain.MessageRepository
	citationRepo     domain.CitationRepository
}

func NewGetConversationUseCase(
	conversationRepo domain.ConversationRepository,
	messageRepo domain.MessageRepository,
	citationRepo domain.CitationRepository,
) *GetConversationUseCase {
	return &GetConversationUseCase{
		conversationRepo: conversationRepo,
		messageRepo:      messageRepo,
		citationRepo:     citationRepo,
	}
}

type GetConversationResponse struct {
	ConversationID uuid.UUID
	Title           string
	Messages        []MessageWithCitations
}

type MessageWithCitations struct {
	ID        uuid.UUID
	Role      string
	Content   string
	Metadata  map[string]interface{}
	Citations []CitationData
	CreatedAt time.Time
}

type CitationData struct {
	ChunkID  string
	SourceID string
	Score    float64
	Quote    string
	Meta     map[string]interface{}
}

func (uc *GetConversationUseCase) Execute(ctx context.Context, conversationID uuid.UUID) (*GetConversationResponse, error) {
	// Получение диалога
	conversation, err := uc.conversationRepo.FindByID(ctx, conversationID)
	if err != nil {
		return nil, fmt.Errorf("conversation not found: %w", err)
	}

	// Получение сообщений
	messages, err := uc.messageRepo.FindByConversationID(ctx, conversationID)
	if err != nil {
		return nil, fmt.Errorf("failed to get messages: %w", err)
	}

	// Формирование ответа с цитатами
	result := &GetConversationResponse{
		ConversationID: conversation.ID,
		Title:           conversation.Title,
		Messages:        make([]MessageWithCitations, 0, len(messages)),
	}

	for _, msg := range messages {
		// Получение цитат для сообщения
		citations, _ := uc.citationRepo.FindByMessageID(ctx, msg.ID)

		citationData := make([]CitationData, 0, len(citations))
		for _, cit := range citations {
			citationData = append(citationData, CitationData{
				ChunkID:  cit.ChunkID,
				SourceID: cit.SourceID,
				Score:    cit.Score,
				Quote:    cit.Quote,
				Meta:     cit.Meta,
			})
		}

		result.Messages = append(result.Messages, MessageWithCitations{
			ID:        msg.ID,
			Role:      msg.Role,
			Content:   msg.Content,
			Metadata:  msg.Metadata,
			Citations: citationData,
			CreatedAt: msg.CreatedAt,
		})
	}

	return result, nil
}

