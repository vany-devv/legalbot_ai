// Package cookie содержит helper'ы и константы для управления HttpOnly
// сессионной cookie. Вынесено в отдельный leaf-пакет, чтобы и middleware,
// и auth/handler могли его импортировать без циклов.
package cookie

import (
	"net/http"
	"time"
)

// SessionCookieName — имя cookie с сессионным токеном (HttpOnly).
const SessionCookieName = "lb-session"

// IsSecureRequest определяет нужно ли ставить Secure-флаг на cookie.
// True если запрос пришёл по HTTPS напрямую (r.TLS != nil) или через
// reverse-proxy с X-Forwarded-Proto: https (nginx с TLS-терминацией).
// Иначе (http://localhost при dev'е) — false, чтобы браузер cookie принял.
func IsSecureRequest(r *http.Request) bool {
	if r.TLS != nil {
		return true
	}
	return r.Header.Get("X-Forwarded-Proto") == "https"
}

// SessionTTL — срок жизни сессии. Sliding-refresh продлевает expires_at каждые
// SlidingThrottle, поэтому фактический срок жизни = пока юзер активен.
const SessionTTL = 20 * 24 * time.Hour

// SlidingThrottle — минимальный интервал между обновлениями expires_at в БД.
// Защита от write-spam на каждом запросе.
const SlidingThrottle = 15 * time.Minute

// SetSession ставит HttpOnly cookie с сессионным токеном.
// secure=true в проде (требует HTTPS), false локально для http://localhost.
func SetSession(w http.ResponseWriter, token string, secure bool) {
	http.SetCookie(w, &http.Cookie{
		Name:     SessionCookieName,
		Value:    token,
		Path:     "/",
		MaxAge:   int(SessionTTL.Seconds()),
		HttpOnly: true,
		Secure:   secure,
		SameSite: http.SameSiteLaxMode,
	})
}

// ClearSession удаляет сессионную cookie на клиенте.
func ClearSession(w http.ResponseWriter, secure bool) {
	http.SetCookie(w, &http.Cookie{
		Name:     SessionCookieName,
		Value:    "",
		Path:     "/",
		MaxAge:   -1,
		HttpOnly: true,
		Secure:   secure,
		SameSite: http.SameSiteLaxMode,
	})
}
