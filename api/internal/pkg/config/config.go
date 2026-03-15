package config

import (
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	Port          string
	DatabaseURL   string
	JWTSecret     string
	Env           string
	RAGServiceURL string
	IngestAPIKey  string
}

func Load() *Config {
	_ = godotenv.Load()

	return &Config{
		Port:          getEnv("PORT", "8080"),
		DatabaseURL:   getEnv("DATABASE_URL", "postgres://user:pass@localhost/legalbot?sslmode=disable"),
		JWTSecret:     getEnv("JWT_SECRET", "change-me-in-production"),
		Env:           getEnv("ENV", "development"),
		RAGServiceURL: getEnv("RAG_SERVICE_URL", "http://localhost:8000"),
		IngestAPIKey:  getEnv("INGEST_API_KEY", ""),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
