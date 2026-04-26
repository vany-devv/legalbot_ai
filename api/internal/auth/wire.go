package auth

import (
	"database/sql"

	"legalbot/services/internal/auth/domain"
	"legalbot/services/internal/auth/handler"
	"legalbot/services/internal/auth/infrastructure"
	"legalbot/services/internal/auth/repository"
	"legalbot/services/internal/auth/usecase"
	billingdomain "legalbot/services/internal/billing/domain"
)

// Module экспортирует handler и репозитории auth-домена.
// UserRepo нужен наружу для admin middleware и orchestrator-bypass.
type Module struct {
	Handler  *handler.AuthHandler
	UserRepo domain.UserRepository
}

func Wire(
	db *sql.DB,
	jwtSecret string,
	planRepo billingdomain.PlanRepository,
	subscriptionRepo billingdomain.SubscriptionRepository,
) *Module {
	// Repositories
	userRepo := repository.NewPostgresUserRepository(db)
	sessionRepo := repository.NewPostgresSessionRepository(db)

	// Infrastructure
	passwordHasher := infrastructure.NewBcryptPasswordHasher()
	tokenGenerator := infrastructure.NewJWTTokenGenerator(jwtSecret)

	// Use cases
	registerUC := usecase.NewRegisterUseCase(userRepo, passwordHasher, planRepo, subscriptionRepo)
	loginUC := usecase.NewLoginUseCase(userRepo, sessionRepo, passwordHasher, tokenGenerator)
	getMeUC := usecase.NewGetMeUseCase(userRepo, tokenGenerator)
	changePasswordUC := usecase.NewChangePasswordUseCase(userRepo, sessionRepo, passwordHasher)

	return &Module{
		Handler:  handler.NewAuthHandler(registerUC, loginUC, getMeUC, changePasswordUC),
		UserRepo: userRepo,
	}
}
