package usecase

import (
	"context"
	"errors"
	"fmt"
	"log"
	"regexp"
	"strings"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/domain"
	billingdomain "legalbot/services/internal/billing/domain"
)

var emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$`)

const FreePlanSlug = "free"

type RegisterUseCase struct {
	userRepo         domain.UserRepository
	passwordHasher   domain.PasswordHasher
	planRepo         billingdomain.PlanRepository
	subscriptionRepo billingdomain.SubscriptionRepository
}

func NewRegisterUseCase(
	userRepo domain.UserRepository,
	passwordHasher domain.PasswordHasher,
	planRepo billingdomain.PlanRepository,
	subscriptionRepo billingdomain.SubscriptionRepository,
) *RegisterUseCase {
	return &RegisterUseCase{
		userRepo:         userRepo,
		passwordHasher:   passwordHasher,
		planRepo:         planRepo,
		subscriptionRepo: subscriptionRepo,
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
	req.Email = strings.TrimSpace(strings.ToLower(req.Email))

	if req.Email == "" || req.Password == "" {
		return nil, errors.New("email and password are required")
	}

	if !emailRegex.MatchString(req.Email) {
		return nil, errors.New("invalid email format")
	}

	if len(req.Password) < 6 {
		return nil, errors.New("password must be at least 6 characters")
	}

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

	// Auto-subscribe на Free-тариф (бесконечная подписка, ExpiresAt = nil)
	if err := uc.subscribeFree(ctx, user.ID); err != nil {
		// Не валим регистрацию, если что-то пошло не так с подпиской — логируем
		// и идём дальше. Бэкфилл-миграция и /api/billing/me лечат такие случаи.
		log.Printf("auth/register: failed to auto-subscribe user %s on Free: %v", user.ID, err)
	}

	return &RegisterResponse{
		UserID: user.ID,
		Email:  user.Email,
	}, nil
}

func (uc *RegisterUseCase) subscribeFree(ctx context.Context, userID uuid.UUID) error {
	plan, err := uc.planRepo.FindBySlug(ctx, FreePlanSlug)
	if err != nil {
		return fmt.Errorf("free plan not found: %w", err)
	}
	now := time.Now()
	sub := &billingdomain.Subscription{
		ID:        uuid.New(),
		UserID:    userID,
		PlanID:    plan.ID,
		Status:    "active",
		StartedAt: now,
		ExpiresAt: nil,
		CreatedAt: now,
		UpdatedAt: now,
	}
	return uc.subscriptionRepo.Create(ctx, sub)
}

