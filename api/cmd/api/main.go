package main

import (
	"log"
	"net/http"

	"legalbot/services/internal/auth"
	"legalbot/services/internal/auth/infrastructure"
	"legalbot/services/internal/billing"
	"legalbot/services/internal/chat"
	"legalbot/services/internal/middleware"
	"legalbot/services/internal/orchestrator"
	"legalbot/services/internal/pkg/config"
	"legalbot/services/internal/pkg/db"
	"legalbot/services/internal/pkg/migrate"
	"legalbot/services/internal/proxy"
	"legalbot/services/internal/ragclient"
)

func main() {
	cfg := config.Load()

	database, err := db.NewPostgres(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer database.Close()

	if err := migrate.Up(database.DB); err != nil {
		log.Fatalf("Migrations failed: %v", err)
	}
	log.Println("Migrations applied successfully")

	mux := http.NewServeMux()

	// Domain modules.
	// Billing должен инициализироваться раньше auth — auth.Wire требует
	// PlanRepo/SubscriptionRepo для авто-подписки на Free при регистрации.
	billingModule := billing.Wire(database.DB)
	billingModule.Handler.RegisterRoutes(mux)

	authModule := auth.Wire(database.DB, cfg.JWTSecret, billingModule.PlanRepo, billingModule.SubscriptionRepo)
	authModule.Handler.RegisterRoutes(mux)

	chatModule := chat.Wire(database.DB)
	chatModule.Handler.RegisterRoutes(mux)

	// RAG proxy: публичные роуты (search, health) и admin-only (ingest, documents).
	ragProxy := proxy.NewRAGProxy(cfg.RAGServiceURL, cfg.IngestAPIKey)
	ragProxy.RegisterPublicRoutes(mux)
	ragProxy.RegisterAdminRoutes(mux, middleware.RequireAdmin(authModule.UserRepo))

	// Orchestrator (POST /api/chat/ask)
	ragClient := ragclient.New(cfg.RAGServiceURL)
	askHandler := orchestrator.NewAskHandler(
		ragClient,
		billingModule.CheckLimits,
		billingModule.RecordUsage,
		chatModule.CreateConversation,
		chatModule.SaveMessage,
		authModule.UserRepo,
	)
	askHandler.RegisterRoutes(mux)

	// Analyze handler (POST /api/analyze/stream)
	analyzeHandler := orchestrator.NewAnalyzeHandler(
		ragClient,
		billingModule.CheckLimits,
		billingModule.RecordUsage,
		authModule.UserRepo,
	)
	analyzeHandler.RegisterRoutes(mux)

	// Auth middleware wraps all routes
	tokenGen := infrastructure.NewJWTTokenGenerator(cfg.JWTSecret)
	publicPaths := []string{
		"/api/auth/register",
		"/api/auth/login",
	}
	handler := middleware.Auth(mux, tokenGen, publicPaths)

	log.Printf("Server starting on :%s (RAG service: %s)\n", cfg.Port, cfg.RAGServiceURL)
	if err := http.ListenAndServe(":"+cfg.Port, handler); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
