package usecase

import (
	"context"
	"errors"
	"fmt"
	"time"

	"legalbot/services/internal/billing/domain"

	"github.com/google/uuid"
)

type CheckLimitsUseCase struct {
	subscriptionRepo domain.SubscriptionRepository
	usageRepo        domain.UsageRepository
	planRepo         domain.PlanRepository
}

func NewCheckLimitsUseCase(
	subscriptionRepo domain.SubscriptionRepository,
	usageRepo domain.UsageRepository,
	planRepo domain.PlanRepository,
) *CheckLimitsUseCase {
	return &CheckLimitsUseCase{
		subscriptionRepo: subscriptionRepo,
		usageRepo:        usageRepo,
		planRepo:         planRepo,
	}
}

type CheckLimitsRequest struct {
	UserID       uuid.UUID
	ResourceType string // requests, documents, tokens
	Amount       int    // сколько нужно использовать
}

type CheckLimitsResponse struct {
	Allowed bool
	Reason  string
	Used    int
	Limit   int
}

func (uc *CheckLimitsUseCase) Execute(ctx context.Context, req CheckLimitsRequest) (*CheckLimitsResponse, error) {
	// Получение подписки
	subscription, err := uc.subscriptionRepo.FindByUserID(ctx, req.UserID)
	if err != nil || subscription.Status != "active" {
		return &CheckLimitsResponse{
			Allowed: false,
			Reason:  "no active subscription",
		}, nil
	}

	// Проверка срока действия
	if time.Now().After(subscription.ExpiresAt) {
		return &CheckLimitsResponse{
			Allowed: false,
			Reason:  "subscription expired",
		}, nil
	}

	// Получение плана
	plan, err := uc.planRepo.FindByID(ctx, subscription.PlanID)
	if err != nil {
		return nil, fmt.Errorf("plan not found: %w", err)
	}

	// Получение использования за текущий период
	periodStart := time.Now().AddDate(0, -1, 0) // последний месяц
	periodEnd := time.Now()

	var limit int
	switch req.ResourceType {
	case "requests":
		limit = plan.MaxRequests
	case "documents":
		limit = plan.MaxDocs
	default:
		return nil, errors.New("unknown resource type")
	}

	usage, _ := uc.usageRepo.GetByUserAndPeriod(ctx, req.UserID, req.ResourceType, periodStart, periodEnd)
	used := 0
	if usage != nil {
		used = usage.Count
	}

	// Проверка лимита
	if used+req.Amount > limit {
		return &CheckLimitsResponse{
			Allowed: false,
			Reason:  "limit exceeded",
			Used:    used,
			Limit:   limit,
		}, nil
	}

	return &CheckLimitsResponse{
		Allowed: true,
		Used:    used,
		Limit:   limit,
	}, nil
}





