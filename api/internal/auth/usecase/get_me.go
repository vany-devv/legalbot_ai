package usecase

import (
	"context"
	"errors"
	"fmt"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/domain"
)

type GetMeUseCase struct {
	userRepo      domain.UserRepository
	tokenGenerator domain.TokenGenerator
}

func NewGetMeUseCase(
	userRepo domain.UserRepository,
	tokenGenerator domain.TokenGenerator,
) *GetMeUseCase {
	return &GetMeUseCase{
		userRepo:      userRepo,
		tokenGenerator: tokenGenerator,
	}
}

type GetMeResponse struct {
	ID    uuid.UUID
	Email string
	Role  string
}

func (uc *GetMeUseCase) Execute(ctx context.Context, token string) (*GetMeResponse, error) {
	// Валидация токена
	userIDStr, err := uc.tokenGenerator.Validate(token)
	if err != nil {
		return nil, errors.New("invalid token")
	}

	userID, err := uuid.Parse(userIDStr)
	if err != nil {
		return nil, errors.New("invalid user ID")
	}

	// Поиск пользователя
	user, err := uc.userRepo.FindByID(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("user not found: %w", err)
	}

	return &GetMeResponse{
		ID:    user.ID,
		Email: user.Email,
		Role:  user.Role,
	}, nil
}

