package billing

import (
	"database/sql"

	"legalbot/services/internal/billing/handler"
	"legalbot/services/internal/billing/infrastructure"
	"legalbot/services/internal/billing/repository"
	"legalbot/services/internal/billing/usecase"
)

type Module struct {
	Handler     *handler.BillingHandler
	CheckLimits *usecase.CheckLimitsUseCase
	RecordUsage *usecase.RecordUsageUseCase
}

func Wire(db *sql.DB) *Module {
	planRepo := repository.NewPostgresPlanRepository(db)
	subscriptionRepo := repository.NewPostgresSubscriptionRepository(db)
	usageRepo := repository.NewPostgresUsageRepository(db)

	paymentProvider := infrastructure.NewStubPaymentProvider()

	createSubscriptionUC := usecase.NewCreateSubscriptionUseCase(planRepo, subscriptionRepo, paymentProvider)
	checkLimitsUC := usecase.NewCheckLimitsUseCase(subscriptionRepo, usageRepo, planRepo)
	recordUsageUC := usecase.NewRecordUsageUseCase(usageRepo)

	return &Module{
		Handler:     handler.NewBillingHandler(createSubscriptionUC, checkLimitsUC, recordUsageUC),
		CheckLimits: checkLimitsUC,
		RecordUsage: recordUsageUC,
	}
}






