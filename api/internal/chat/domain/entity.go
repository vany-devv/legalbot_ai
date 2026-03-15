package domain

import (
	"time"

	"github.com/google/uuid"
)

// Conversation представляет диалог пользователя
type Conversation struct {
	ID        uuid.UUID
	UserID    uuid.UUID
	Title     string
	CreatedAt time.Time
	UpdatedAt time.Time
}

// Message представляет сообщение в диалоге
type Message struct {
	ID             uuid.UUID
	ConversationID uuid.UUID
	Role           string // user, assistant
	Content        string
	Metadata       map[string]interface{} // provider, model, confidence и т.д.
	CreatedAt      time.Time
}

// Citation представляет цитату из RAG
type Citation struct {
	ID             uuid.UUID
	MessageID      uuid.UUID
	ChunkID        string
	SourceID       string
	Score          float64
	Quote          string
	Meta           map[string]interface{} // act, article и т.д.
	CreatedAt      time.Time
}






