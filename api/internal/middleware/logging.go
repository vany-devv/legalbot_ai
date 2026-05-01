package middleware

import (
	"net/http"
	"time"

	"github.com/google/uuid"

	"legalbot/services/internal/pkg/logger"
)

const requestIDHeader = "X-Request-ID"

// RequestID middleware: читает X-Request-ID из заголовка либо генерит uuid,
// кладёт его в контекст вместе с дочерним логгером, эхом возвращает в ответе.
func RequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rid := r.Header.Get(requestIDHeader)
		if rid == "" {
			rid = uuid.NewString()
		}

		ctx := logger.WithRequestID(r.Context(), rid)
		ctx = logger.WithAttrs(ctx, "request_id", rid)

		w.Header().Set(requestIDHeader, rid)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// statusRecorder перехватывает статус и количество записанных байт.
type statusRecorder struct {
	http.ResponseWriter
	status int
	bytes  int
}

func (s *statusRecorder) WriteHeader(code int) {
	s.status = code
	s.ResponseWriter.WriteHeader(code)
}

func (s *statusRecorder) Write(b []byte) (int, error) {
	if s.status == 0 {
		s.status = http.StatusOK
	}
	n, err := s.ResponseWriter.Write(b)
	s.bytes += n
	return n, err
}

// Flush для совместимости с SSE-обработчиками.
func (s *statusRecorder) Flush() {
	if f, ok := s.ResponseWriter.(http.Flusher); ok {
		f.Flush()
	}
}

// Access middleware: на каждый HTTP-запрос пишет одну строку с методом, путём,
// статусом и длительностью. WARN для 4xx, ERROR для 5xx, INFO иначе.
func Access(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rec := &statusRecorder{ResponseWriter: w, status: http.StatusOK}

		next.ServeHTTP(rec, r)

		duration := time.Since(start)
		log := logger.FromCtx(r.Context())

		attrs := []any{
			"method", r.Method,
			"path", r.URL.Path,
			"status", rec.status,
			"duration_ms", duration.Milliseconds(),
			"remote_addr", clientIP(r),
		}
		if userID, ok := GetUserID(r.Context()); ok {
			attrs = append(attrs, "user_id", userID)
		}

		switch {
		case rec.status >= 500:
			log.Error("http_request", attrs...)
		case rec.status >= 400:
			log.Warn("http_request", attrs...)
		default:
			log.Info("http_request", attrs...)
		}
	})
}

func clientIP(r *http.Request) string {
	if v := r.Header.Get("X-Forwarded-For"); v != "" {
		return v
	}
	return r.RemoteAddr
}
