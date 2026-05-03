package middleware

import (
	"context"
	"net/http"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/cookie"
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

		c, err := r.Cookie(cookie.SessionCookieName)
		if err != nil || c.Value == "" {
			log.Warn("auth_failed", "reason", "missing_cookie")
			http.Error(w, "authorization required", http.StatusUnauthorized)
			return
		}
		token := c.Value

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

		// Sliding refresh: продлеваем expires_at если с прошлого обновления
		// прошло > SlidingThrottle. Так избегаем write-spam в БД при активной сессии.
		now := time.Now()
		newExpiresAt := now.Add(cookie.SessionTTL)
		// session.ExpiresAt = lastRefresh + SessionTTL → lastRefresh = session.ExpiresAt - SessionTTL
		// если новое значение больше старого на > SlidingThrottle, обновляем.
		if newExpiresAt.Sub(session.ExpiresAt) > cookie.SlidingThrottle {
			if err := sessionRepo.RefreshExpiry(ctx, session.ID, newExpiresAt); err != nil {
				log.Warn("session_refresh_failed", "err", err.Error(), "user_id", userID)
				// не прерываем запрос — sliding неудача не должна логаутить юзера
			} else {
				cookie.SetSession(w, token, cookie.IsSecureRequest(r))
			}
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
