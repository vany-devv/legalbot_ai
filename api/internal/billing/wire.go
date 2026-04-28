package billing

import (
	"database/sql"

	"legalbot/services/internal/billing/domain"
	"legalbot/services/internal/billing/handler"
	"legalbot/services/internal/billing/infrastructure"
	"legalbot/services/internal/billing/repository"
	"legalbot/services/internal/billing/usecase"
)

type Module struct {
	Handler          *handler.BillingHandler
	CheckLimits      *usecase.CheckLimitsUseCase
	RecordUsage      *usecase.RecordUsageUseCase
	PlanRepo         domain.PlanRepository
	SubscriptionRepo domain.SubscriptionRepository
}

func Wire(db *sql.DB) *Module {
	planRepo := repository.NewPostgresPlanRepository(db)
	subscriptionRepo := repository.NewPostgresSubscriptionRepository(db)
	usageRepo := repository.NewPostgresUsageRepository(db)

	paymentProvider := infrastructure.NewStubPaymentProvider()

	createSubscriptionUC := usecase.NewCreateSubscriptionUseCase(planRepo, subscriptionRepo, paymentProvider)
	checkLimitsUC := usecase.NewCheckLimitsUseCase(subscriptionRepo, usageRepo, planRepo)
	recordUsageUC := usecase.NewRecordUsageUseCase(usageRepo)
	getUserBillingUC := usecase.NewGetUserBillingUseCase(subscriptionRepo, planRepo, usageRepo)

	return &Module{
		Handler:          handler.NewBillingHandler(createSubscriptionUC, checkLimitsUC, recordUsageUC, getUserBillingUC),
		CheckLimits:      checkLimitsUC,
		RecordUsage:      recordUsageUC,
		PlanRepo:         planRepo,
		SubscriptionRepo: subscriptionRepo,
	}
}
