package middleware

import (
	"net/http"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/domain"
	"legalbot/services/internal/auth/usecase"
)

// RequireAdmin оборачивает обработчик и пропускает только пользователей с ролью admin.
// Делает FindByID на каждый запрос — применять только к редким admin-эндпоинтам.
func RequireAdmin(userRepo domain.UserRepository) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			userIDStr, ok := GetUserID(r.Context())
			if !ok || userIDStr == "" {
				http.Error(w, "unauthorized", http.StatusUnauthorized)
				return
			}
			userID, err := uuid.Parse(userIDStr)
			if err != nil {
				http.Error(w, "unauthorized", http.StatusUnauthorized)
				return
			}
			if !usecase.IsAdmin(r.Context(), userRepo, userID) {
				http.Error(w, "forbidden", http.StatusForbidden)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
