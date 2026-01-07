package usecase

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/domain"
)

type RegisterUseCase struct {
	userRepo      domain.UserRepository
	passwordHasher domain.PasswordHasher
}

func NewRegisterUseCase(
	userRepo domain.UserRepository,
	passwordHasher domain.PasswordHasher,
) *RegisterUseCase {
	return &RegisterUseCase{
		userRepo:      userRepo,
		passwordHasher: passwordHasher,
	}
}

type RegisterRequest struct {
	Email    string
	Password string
}

type RegisterResponse struct {
	UserID uuid.UUID
	Email  string
}

func (uc *RegisterUseCase) Execute(ctx context.Context, req RegisterRequest) (*RegisterResponse, error) {
	// Валидация
	if req.Email == "" || req.Password == "" {
		return nil, errors.New("email and password are required")
	}

	// Проверка существования пользователя
	existing, _ := uc.userRepo.FindByEmail(ctx, req.Email)
	if existing != nil {
		return nil, errors.New("user with this email already exists")
	}

	// Хэширование пароля
	hashedPassword, err := uc.passwordHasher.Hash(req.Password)
	if err != nil {
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}

	// Создание пользователя
	user := &domain.User{
		ID:           uuid.New(),
		Email:        req.Email,
		PasswordHash: hashedPassword,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	if err := uc.userRepo.Create(ctx, user); err != nil {
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	return &RegisterResponse{
		UserID: user.ID,
		Email:  user.Email,
	}, nil
}

