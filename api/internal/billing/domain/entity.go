package domain

import (
	"time"

	"github.com/google/uuid"
)

// Plan представляет тарифный план
type Plan struct {
	ID          uuid.UUID
	Name        string
	Price       int64 // в копейках
	MaxRequests int   // лимит запросов в месяц
	MaxDocs     int   // лимит документов
	Features    []string
	CreatedAt   time.Time
}

// Subscription представляет подписку пользователя
type Subscription struct {
	ID        uuid.UUID
	UserID    uuid.UUID
	PlanID    uuid.UUID
	Status    string // active, cancelled, expired
	StartedAt time.Time
	ExpiresAt time.Time
	CreatedAt time.Time
	UpdatedAt time.Time
}

// Usage представляет использование ресурсов
type Usage struct {
	ID            uuid.UUID
	UserID        uuid.UUID
	ResourceType  string // requests, documents, tokens
	Count         int
	PeriodStart   time.Time
	PeriodEnd     time.Time
	CreatedAt     time.Time
}

