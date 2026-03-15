package auth

import (
	"database/sql"

	"legalbot/services/internal/auth/handler"
	"legalbot/services/internal/auth/infrastructure"
	"legalbot/services/internal/auth/repository"
	"legalbot/services/internal/auth/usecase"
)

// Wire собирает все зависимости домена auth
func Wire(db *sql.DB, jwtSecret string) *handler.AuthHandler {
	// Repositories
	userRepo := repository.NewPostgresUserRepository(db)
	sessionRepo := repository.NewPostgresSessionRepository(db)

	// Infrastructure
	passwordHasher := infrastructure.NewBcryptPasswordHasher()
	tokenGenerator := infrastructure.NewJWTTokenGenerator(jwtSecret)

	// Use cases
	registerUC := usecase.NewRegisterUseCase(userRepo, passwordHasher)
	loginUC := usecase.NewLoginUseCase(userRepo, sessionRepo, passwordHasher, tokenGenerator)
	getMeUC := usecase.NewGetMeUseCase(userRepo, tokenGenerator)

	// Handler
	return handler.NewAuthHandler(registerUC, loginUC, getMeUC)
}

