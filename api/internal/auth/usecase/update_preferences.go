package usecase

import (
	"context"
	"errors"
	"fmt"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/domain"
)

type UpdatePreferencesUseCase struct {
	userRepo domain.UserRepository
}

func NewUpdatePreferencesUseCase(userRepo domain.UserRepository) *UpdatePreferencesUseCase {
	return &UpdatePreferencesUseCase{userRepo: userRepo}
}

// UpdatePreferencesRequest — partial update. Поля-указатели:
// nil = "не трогать", non-nil = новое значение.
type UpdatePreferencesRequest struct {
	UserID           uuid.UUID
	PreferredPalette *string
}

func (uc *UpdatePreferencesUseCase) Execute(ctx context.Context, req UpdatePreferencesRequest) (*domain.User, error) {
	user, err := uc.userRepo.FindByID(ctx, req.UserID)
	if err != nil {
		return nil, fmt.Errorf("user not found: %w", err)
	}

	if req.PreferredPalette != nil {
		palette := *req.PreferredPalette
		if _, ok := domain.ValidPalettes[palette]; !ok {
			return nil, errors.New("invalid palette")
		}
		user.PreferredPalette = palette
	}

	if err := uc.userRepo.Update(ctx, user); err != nil {
		return nil, fmt.Errorf("failed to update user: %w", err)
	}

	return user, nil
}
