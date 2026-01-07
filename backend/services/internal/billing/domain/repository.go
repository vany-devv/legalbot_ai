package domain

import (
	"context"
	"time"

	"github.com/google/uuid"
)

// PlanRepository определяет интерфейс для работы с тарифами
type PlanRepository interface {
	FindByID(ctx context.Context, id uuid.UUID) (*Plan, error)
	FindAll(ctx context.Context) ([]*Plan, error)
}

// SubscriptionRepository определяет интерфейс для работы с подписками
type SubscriptionRepository interface {
	Create(ctx context.Context, sub *Subscription) error
	FindByUserID(ctx context.Context, userID uuid.UUID) (*Subscription, error)
	FindByID(ctx context.Context, id uuid.UUID) (*Subscription, error)
	Update(ctx context.Context, sub *Subscription) error
	Cancel(ctx context.Context, id uuid.UUID) error
}

// UsageRepository определяет интерфейс для работы с использованием
type UsageRepository interface {
	Create(ctx context.Context, usage *Usage) error
	GetByUserAndPeriod(ctx context.Context, userID uuid.UUID, resourceType string, start, end time.Time) (*Usage, error)
	Increment(ctx context.Context, userID uuid.UUID, resourceType string, count int) error
}

// InvoiceRepository определяет интерфейс для работы со счетами
type InvoiceRepository interface {
	Create(ctx context.Context, invoice *Invoice) error
	FindByID(ctx context.Context, id uuid.UUID) (*Invoice, error)
	FindByUserID(ctx context.Context, userID uuid.UUID) ([]*Invoice, error)
	UpdateStatus(ctx context.Context, id uuid.UUID, status string) error
}

