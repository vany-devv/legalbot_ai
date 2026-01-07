package main

import (
	"log"
	"net/http"

	"legalbot/services/internal/auth"
	"legalbot/services/internal/billing"
	"legalbot/services/internal/chat"
	"legalbot/services/internal/pkg/config"
	"legalbot/services/internal/pkg/db"
)

func main() {
	cfg := config.Load()

	database, err := db.NewPostgres(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer database.Close()

	mux := http.NewServeMux()

	authHandler := auth.Wire(database.DB, cfg.JWTSecret)
	authHandler.RegisterRoutes(mux)

	billingHandler := billing.Wire(database.DB)
	billingHandler.RegisterRoutes(mux)

	chatHandler := chat.Wire(database.DB)
	chatHandler.RegisterRoutes(mux)

	log.Printf("Server starting on :%s\n", cfg.Port)
	if err := http.ListenAndServe(":"+cfg.Port, mux); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
