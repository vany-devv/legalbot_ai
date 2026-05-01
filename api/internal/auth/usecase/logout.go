package usecase

import (
	"context"

	"legalbot/services/internal/auth/domain"
	"legalbot/services/internal/pkg/logger"
)

type LogoutUseCase struct {
	sessionRepo domain.SessionRepository
}

func NewLogoutUseCase(sessionRepo domain.SessionRepository) *LogoutUseCase {
	return &LogoutUseCase{sessionRepo: sessionRepo}
}

func (uc *LogoutUseCase) Execute(ctx context.Context, token string) error {
	session, err := uc.sessionRepo.FindByToken(ctx, token)
	if err != nil {
		return err
	}
	if err := uc.sessionRepo.Delete(ctx, session.ID); err != nil {
		return err
	}
	logger.FromCtx(ctx).Info("logout", "user_id", session.UserID.String())
	return nil
}
