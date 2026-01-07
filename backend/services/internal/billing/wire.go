package billing

import (
	"database/sql"

	"legalbot/services/internal/billing/handler"
	"legalbot/services/internal/billing/infrastructure"
	"legalbot/services/internal/billing/repository"
	"legalbot/services/internal/billing/usecase"
)

// Wire собирает все зависимости домена billing
func Wire(db *sql.DB) *handler.BillingHandler {
	// Repositories
	planRepo := repository.NewPostgresPlanRepository(db)
	subscriptionRepo := repository.NewPostgresSubscriptionRepository(db)
	usageRepo := repository.NewPostgresUsageRepository(db)

	// Infrastructure
	paymentProvider := infrastructure.NewStubPaymentProvider()

	// Use cases
	createSubscriptionUC := usecase.NewCreateSubscriptionUseCase(planRepo, subscriptionRepo, paymentProvider)
	checkLimitsUC := usecase.NewCheckLimitsUseCase(subscriptionRepo, usageRepo, planRepo)
	recordUsageUC := usecase.NewRecordUsageUseCase(usageRepo)

	// Handler
	return handler.NewBillingHandler(createSubscriptionUC, checkLimitsUC, recordUsageUC)
}






