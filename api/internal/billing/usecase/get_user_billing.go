package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/billing/domain"
)

type GetUserBillingUseCase struct {
	subscriptionRepo domain.SubscriptionRepository
	planRepo         domain.PlanRepository
	usageRepo        domain.UsageRepository
}

func NewGetUserBillingUseCase(
	subscriptionRepo domain.SubscriptionRepository,
	planRepo domain.PlanRepository,
	usageRepo domain.UsageRepository,
) *GetUserBillingUseCase {
	return &GetUserBillingUseCase{
		subscriptionRepo: subscriptionRepo,
		planRepo:         planRepo,
		usageRepo:        usageRepo,
	}
}

type UserBillingResponse struct {
	PlanSlug      string     `json:"plan_slug"`
	PlanName      string     `json:"plan_name"`
	Status        string     `json:"status"`
	UsedRequests  int        `json:"used_requests"`
	LimitRequests int        `json:"limit_requests"`
	ExpiresAt     *time.Time `json:"expires_at"`
}

func (uc *GetUserBillingUseCase) Execute(ctx context.Context, userID uuid.UUID) (*UserBillingResponse, error) {
	sub, err := uc.subscriptionRepo.FindByUserID(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("subscription not found: %w", err)
	}

	plan, err := uc.planRepo.FindByID(ctx, sub.PlanID)
	if err != nil {
		return nil, fmt.Errorf("plan not found: %w", err)
	}

	periodStart := time.Now().AddDate(0, -1, 0)
	periodEnd := time.Now()
	used := 0
	if usage, _ := uc.usageRepo.GetByUserAndPeriod(ctx, userID, "requests", periodStart, periodEnd); usage != nil {
		used = usage.Count
	}

	return &UserBillingResponse{
		PlanSlug:      plan.Slug,
		PlanName:      plan.Name,
		Status:        sub.Status,
		UsedRequests:  used,
		LimitRequests: plan.MaxRequests,
		ExpiresAt:     sub.ExpiresAt,
	}, nil
}
