package middleware

import (
	"net/http"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/domain"
	"legalbot/services/internal/auth/usecase"
	"legalbot/services/internal/pkg/logger"
)

// RequireAdmin оборачивает обработчик и пропускает только пользователей с ролью admin.
// Делает FindByID на каждый запрос — применять только к редким admin-эндпоинтам.
func RequireAdmin(userRepo domain.UserRepository) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx := r.Context()
			log := logger.FromCtx(ctx)
			userIDStr, ok := GetUserID(ctx)
			if !ok || userIDStr == "" {
				log.Warn("admin_access_denied", "reason", "no_user")
				http.Error(w, "unauthorized", http.StatusUnauthorized)
				return
			}
			userID, err := uuid.Parse(userIDStr)
			if err != nil {
				log.Warn("admin_access_denied", "reason", "bad_user_id", "user_id", userIDStr)
				http.Error(w, "unauthorized", http.StatusUnauthorized)
				return
			}
			if !usecase.IsAdmin(ctx, userRepo, userID) {
				log.Warn("admin_access_denied", "reason", "not_admin", "user_id", userIDStr)
				http.Error(w, "forbidden", http.StatusForbidden)
				return
			}
			log.Debug("admin_access_granted", "user_id", userIDStr)
			next.ServeHTTP(w, r)
		})
	}
}
