package usecase

import (
	"context"

	"github.com/google/uuid"
	"legalbot/services/internal/billing/domain"
)

type RecordUsageUseCase struct {
	usageRepo domain.UsageRepository
}

func NewRecordUsageUseCase(usageRepo domain.UsageRepository) *RecordUsageUseCase {
	return &RecordUsageUseCase{usageRepo: usageRepo}
}

type RecordUsageRequest struct {
	UserID       uuid.UUID
	ResourceType string
	Amount       int
}

func (uc *RecordUsageUseCase) Execute(ctx context.Context, req RecordUsageRequest) error {
	// Инкремент использования (создает или обновляет запись)
	return uc.usageRepo.Increment(ctx, req.UserID, req.ResourceType, req.Amount)
}






