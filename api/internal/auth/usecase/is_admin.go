package usecase

import (
	"context"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/domain"
)

// IsAdmin делает ленивый lookup роли в БД. Возвращает false при любой ошибке
// (юзер не найден, БД недоступна и т.п.) — это безопасный default для admin-флоу.
func IsAdmin(ctx context.Context, userRepo domain.UserRepository, userID uuid.UUID) bool {
	user, err := userRepo.FindByID(ctx, userID)
	if err != nil {
		return false
	}
	return user.Role == domain.RoleAdmin
}
