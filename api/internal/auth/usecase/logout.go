package usecase

import (
	"context"

	"legalbot/services/internal/auth/domain"
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
	return uc.sessionRepo.Delete(ctx, session.ID)
}
