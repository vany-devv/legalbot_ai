package domain

import (
	"time"

	"github.com/google/uuid"
)

const (
	RoleUser  = "user"
	RoleAdmin = "admin"
)

// Допустимые палитры. Должны соответствовать списку в frontend/composables/usePalette.ts.
var ValidPalettes = map[string]struct{}{
	"indigo":   {},
	"navy":     {},
	"bordeaux": {},
	"emerald":  {},
	"graphite": {},
}

const DefaultPalette = "navy"

// User представляет пользователя системы
type User struct {
	ID               uuid.UUID
	Email            string
	PasswordHash     string
	Role             string
	PreferredPalette string
	CreatedAt        time.Time
	UpdatedAt        time.Time
}

// Token представляет JWT токен
type Token struct {
	AccessToken  string
	RefreshToken string
	ExpiresAt    time.Time
}

// Session представляет сессию пользователя
type Session struct {
	ID        uuid.UUID
	UserID    uuid.UUID
	Token     string
	ExpiresAt time.Time
	CreatedAt time.Time
}
