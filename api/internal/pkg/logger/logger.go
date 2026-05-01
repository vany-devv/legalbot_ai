// Package logger предоставляет настройку структурного логгера на базе log/slog
// и хелперы для проброса логгера и request-id через context.Context.
package logger

import (
	"context"
	"log/slog"
	"os"
	"strings"
)

type ctxKey int

const (
	loggerKey ctxKey = iota
	requestIDKey
)

// New создаёт slog.Logger с уровнем из LOG_LEVEL и форматом из LOG_FORMAT.
// env используется как дефолт формата: dev → text, остальное → json.
func New(env string) *slog.Logger {
	opts := &slog.HandlerOptions{Level: parseLevel(os.Getenv("LOG_LEVEL"))}

	format := strings.ToLower(os.Getenv("LOG_FORMAT"))
	if format == "" {
		if strings.HasPrefix(strings.ToLower(env), "dev") {
			format = "text"
		} else {
			format = "json"
		}
	}

	var handler slog.Handler
	if format == "text" {
		handler = slog.NewTextHandler(os.Stdout, opts)
	} else {
		handler = slog.NewJSONHandler(os.Stdout, opts)
	}

	return slog.New(handler).With("service", "api")
}

func parseLevel(s string) slog.Level {
	switch strings.ToLower(s) {
	case "debug":
		return slog.LevelDebug
	case "warn", "warning":
		return slog.LevelWarn
	case "error":
		return slog.LevelError
	default:
		return slog.LevelInfo
	}
}

// FromCtx возвращает логгер из контекста или slog.Default(), если его там нет.
func FromCtx(ctx context.Context) *slog.Logger {
	if l, ok := ctx.Value(loggerKey).(*slog.Logger); ok && l != nil {
		return l
	}
	return slog.Default()
}

// WithCtx кладёт логгер в контекст.
func WithCtx(ctx context.Context, l *slog.Logger) context.Context {
	return context.WithValue(ctx, loggerKey, l)
}

// WithAttrs возвращает контекст с логгером, обогащённым переданными атрибутами.
func WithAttrs(ctx context.Context, args ...any) context.Context {
	return WithCtx(ctx, FromCtx(ctx).With(args...))
}

// RequestID возвращает request-id из контекста (пустая строка если нет).
func RequestID(ctx context.Context) string {
	if id, ok := ctx.Value(requestIDKey).(string); ok {
		return id
	}
	return ""
}

// WithRequestID кладёт request-id в контекст.
func WithRequestID(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, requestIDKey, id)
}
