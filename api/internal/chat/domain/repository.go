package domain

import (
	"context"

	"github.com/google/uuid"
)

// ConversationRepository определяет интерфейс для работы с диалогами
type ConversationRepository interface {
	Create(ctx context.Context, conv *Conversation) error
	FindByID(ctx context.Context, id uuid.UUID) (*Conversation, error)
	FindByUserID(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*Conversation, error)
	Update(ctx context.Context, conv *Conversation) error
	Delete(ctx context.Context, id uuid.UUID) error
}

// MessageRepository определяет интерфейс для работы с сообщениями
type MessageRepository interface {
	Create(ctx context.Context, msg *Message) error
	FindByConversationID(ctx context.Context, conversationID uuid.UUID) ([]*Message, error)
	FindByID(ctx context.Context, id uuid.UUID) (*Message, error)
	Delete(ctx context.Context, id uuid.UUID) error
}

// CitationRepository определяет интерфейс для работы с цитатами
type CitationRepository interface {
	Create(ctx context.Context, citation *Citation) error
	FindByMessageID(ctx context.Context, messageID uuid.UUID) ([]*Citation, error)
	DeleteByMessageID(ctx context.Context, messageID uuid.UUID) error
}






