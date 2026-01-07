package domain

import (
	"context"

	"github.com/google/uuid"
)

// UserRepository определяет интерфейс для работы с пользователями
type UserRepository interface {
	Create(ctx context.Context, user *User) error
	FindByID(ctx context.Context, id uuid.UUID) (*User, error)
	FindByEmail(ctx context.Context, email string) (*User, error)
	Update(ctx context.Context, user *User) error
	Delete(ctx context.Context, id uuid.UUID) error
}

// SessionRepository определяет интерфейс для работы с сессиями
type SessionRepository interface {
	Create(ctx context.Context, session *Session) error
	FindByToken(ctx context.Context, token string) (*Session, error)
	Delete(ctx context.Context, id uuid.UUID) error
	DeleteByUserID(ctx context.Context, userID uuid.UUID) error
}

