package usecase

import (
	"context"
	"errors"
	"fmt"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/domain"
	"legalbot/services/internal/pkg/logger"
)

type ChangePasswordUseCase struct {
	userRepo       domain.UserRepository
	sessionRepo    domain.SessionRepository
	passwordHasher domain.PasswordHasher
}

func NewChangePasswordUseCase(
	userRepo domain.UserRepository,
	sessionRepo domain.SessionRepository,
	passwordHasher domain.PasswordHasher,
) *ChangePasswordUseCase {
	return &ChangePasswordUseCase{
		userRepo:       userRepo,
		sessionRepo:    sessionRepo,
		passwordHasher: passwordHasher,
	}
}

type ChangePasswordRequest struct {
	UserID          uuid.UUID
	CurrentPassword string
	NewPassword     string
}

func (uc *ChangePasswordUseCase) Execute(ctx context.Context, req ChangePasswordRequest) error {
	if req.CurrentPassword == "" || req.NewPassword == "" {
		return errors.New("current password and new password are required")
	}

	if len(req.NewPassword) < 6 {
		return errors.New("new password must be at least 6 characters")
	}

	user, err := uc.userRepo.FindByID(ctx, req.UserID)
	if err != nil {
		return errors.New("user not found")
	}

	if err := uc.passwordHasher.Compare(user.PasswordHash, req.CurrentPassword); err != nil {
		logger.FromCtx(ctx).Warn("change_password_failed", "reason", "bad_current", "user_id", req.UserID.String())
		return errors.New("current password is incorrect")
	}

	hashedPassword, err := uc.passwordHasher.Hash(req.NewPassword)
	if err != nil {
		return fmt.Errorf("failed to hash password: %w", err)
	}

	user.PasswordHash = hashedPassword
	if err := uc.userRepo.Update(ctx, user); err != nil {
		return fmt.Errorf("failed to update password: %w", err)
	}

	_ = uc.sessionRepo.DeleteByUserID(ctx, req.UserID)

	logger.FromCtx(ctx).Info("password_changed", "user_id", req.UserID.String())
	return nil
}
