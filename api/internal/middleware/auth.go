package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/domain"
	"legalbot/services/internal/pkg/logger"
)

type contextKey string

const UserIDKey contextKey = "userID"

func Auth(
	next http.Handler,
	tokenGen domain.TokenGenerator,
	sessionRepo domain.SessionRepository,
	publicPaths []string,
) http.Handler {
	public := make(map[string]bool, len(publicPaths))
	for _, p := range publicPaths {
		public[p] = true
	}

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if public[r.URL.Path] {
			next.ServeHTTP(w, r)
			return
		}

		ctx := r.Context()
		log := logger.FromCtx(ctx)

		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			log.Warn("auth_failed", "reason", "missing_header")
			http.Error(w, "authorization required", http.StatusUnauthorized)
			return
		}

		token := strings.TrimPrefix(authHeader, "Bearer ")
		if token == authHeader {
			log.Warn("auth_failed", "reason", "invalid_format")
			http.Error(w, "invalid authorization format", http.StatusUnauthorized)
			return
		}

		userID, err := tokenGen.Validate(token)
		if err != nil {
			log.Warn("auth_failed", "reason", "invalid_token")
			http.Error(w, "invalid or expired token", http.StatusUnauthorized)
			return
		}

		session, err := sessionRepo.FindByToken(ctx, token)
		if err != nil {
			log.Warn("auth_failed", "reason", "session_not_found", "user_id", userID)
			http.Error(w, "invalid or expired session", http.StatusUnauthorized)
			return
		}

		sessionUserID := session.UserID.String()
		if _, err := uuid.Parse(userID); err != nil || sessionUserID != userID {
			log.Warn("auth_failed", "reason", "session_user_mismatch", "user_id", userID)
			http.Error(w, "invalid session", http.StatusUnauthorized)
			return
		}

		ctx = context.WithValue(ctx, UserIDKey, userID)
		ctx = logger.WithAttrs(ctx, "user_id", userID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func GetUserID(ctx context.Context) (string, bool) {
	userID, ok := ctx.Value(UserIDKey).(string)
	return userID, ok
}
