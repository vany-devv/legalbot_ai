package usecase

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/domain"
)

type GetMeUseCase struct {
	userRepo domain.UserRepository
}

func NewGetMeUseCase(userRepo domain.UserRepository) *GetMeUseCase {
	return &GetMeUseCase{userRepo: userRepo}
}

type GetMeResponse struct {
	ID               uuid.UUID
	Email            string
	Role             string
	PreferredPalette string
}

// Execute грузит профиль юзера по ID. ID берётся из контекста запроса
// (auth-middleware валидирует cookie + DB-сессию и кладёт user_id в ctx).
func (uc *GetMeUseCase) Execute(ctx context.Context, userID uuid.UUID) (*GetMeResponse, error) {
	user, err := uc.userRepo.FindByID(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("user not found: %w", err)
	}

	return &GetMeResponse{
		ID:               user.ID,
		Email:            user.Email,
		Role:             user.Role,
		PreferredPalette: user.PreferredPalette,
	}, nil
}
