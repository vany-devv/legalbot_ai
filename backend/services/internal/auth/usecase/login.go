package usecase

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/domain"
)

type LoginUseCase struct {
	userRepo      domain.UserRepository
	sessionRepo   domain.SessionRepository
	passwordHasher domain.PasswordHasher
	tokenGenerator domain.TokenGenerator
}

func NewLoginUseCase(
	userRepo domain.UserRepository,
	sessionRepo domain.SessionRepository,
	passwordHasher domain.PasswordHasher,
	tokenGenerator domain.TokenGenerator,
) *LoginUseCase {
	return &LoginUseCase{
		userRepo:      userRepo,
		sessionRepo:   sessionRepo,
		passwordHasher: passwordHasher,
		tokenGenerator: tokenGenerator,
	}
}

type LoginRequest struct {
	Email    string
	Password string
}

type LoginResponse struct {
	Token     string
	UserID    uuid.UUID
	ExpiresAt time.Time
}

func (uc *LoginUseCase) Execute(ctx context.Context, req LoginRequest) (*LoginResponse, error) {
	// Поиск пользователя
	user, err := uc.userRepo.FindByEmail(ctx, req.Email)
	if err != nil {
		return nil, errors.New("invalid credentials")
	}

	// Проверка пароля
	if err := uc.passwordHasher.Compare(user.PasswordHash, req.Password); err != nil {
		return nil, errors.New("invalid credentials")
	}

	// Генерация токена
	token, err := uc.tokenGenerator.Generate(user.ID.String())
	if err != nil {
		return nil, fmt.Errorf("failed to generate token: %w", err)
	}

	// Создание сессии
	session := &domain.Session{
		ID:        uuid.New(),
		UserID:    user.ID,
		Token:     token,
		ExpiresAt: time.Now().Add(24 * time.Hour),
		CreatedAt: time.Now(),
	}

	if err := uc.sessionRepo.Create(ctx, session); err != nil {
		return nil, fmt.Errorf("failed to create session: %w", err)
	}

	return &LoginResponse{
		Token:     token,
		UserID:    user.ID,
		ExpiresAt: session.ExpiresAt,
	}, nil
}

