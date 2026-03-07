package usecase

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/billing/domain"
)

type CreateSubscriptionUseCase struct {
	planRepo         domain.PlanRepository
	subscriptionRepo domain.SubscriptionRepository
	paymentProvider  domain.PaymentProvider
}

func NewCreateSubscriptionUseCase(
	planRepo domain.PlanRepository,
	subscriptionRepo domain.SubscriptionRepository,
	paymentProvider domain.PaymentProvider,
) *CreateSubscriptionUseCase {
	return &CreateSubscriptionUseCase{
		planRepo:         planRepo,
		subscriptionRepo: subscriptionRepo,
		paymentProvider:  paymentProvider,
	}
}

type CreateSubscriptionRequest struct {
	UserID uuid.UUID
	PlanID uuid.UUID
}

type CreateSubscriptionResponse struct {
	SubscriptionID uuid.UUID
	PlanID         uuid.UUID
	Status         string
	ExpiresAt      time.Time
}

func (uc *CreateSubscriptionUseCase) Execute(ctx context.Context, req CreateSubscriptionRequest) (*CreateSubscriptionResponse, error) {
	// Проверка существования плана
	plan, err := uc.planRepo.FindByID(ctx, req.PlanID)
	if err != nil {
		return nil, errors.New("plan not found")
	}

	// Проверка существующей подписки
	existing, _ := uc.subscriptionRepo.FindByUserID(ctx, req.UserID)
	if existing != nil && existing.Status == "active" {
		return nil, errors.New("user already has active subscription")
	}

	// Создание платежа (stub — результат пока не используется)
	if _, err := uc.paymentProvider.CreatePayment(plan.Price, "RUB", req.UserID.String()); err != nil {
		return nil, fmt.Errorf("failed to create payment: %w", err)
	}

	// Создание подписки
	now := time.Now()
	subscription := &domain.Subscription{
		ID:        uuid.New(),
		UserID:    req.UserID,
		PlanID:    req.PlanID,
		Status:    "pending", // станет active после подтверждения платежа
		StartedAt: now,
		ExpiresAt: now.AddDate(0, 1, 0), // 1 месяц
		CreatedAt: now,
		UpdatedAt: now,
	}

	if err := uc.subscriptionRepo.Create(ctx, subscription); err != nil {
		return nil, fmt.Errorf("failed to create subscription: %w", err)
	}

	return &CreateSubscriptionResponse{
		SubscriptionID: subscription.ID,
		PlanID:         subscription.PlanID,
		Status:         subscription.Status,
		ExpiresAt:      subscription.ExpiresAt,
	}, nil
}

