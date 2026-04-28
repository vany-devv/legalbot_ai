package proxy

import (
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
)

type RAGProxy struct {
	proxy *httputil.ReverseProxy
}

func NewRAGProxy(rawURL string, ingestAPIKey string) *RAGProxy {
	target, _ := url.Parse(rawURL)

	proxy := httputil.NewSingleHostReverseProxy(target)

	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalDirector(req)
		req.URL.Path = strings.TrimPrefix(req.URL.Path, "/api/rag")
		req.Host = target.Host
		if ingestAPIKey != "" {
			req.Header.Set("X-Api-Key", ingestAPIKey)
		}
	}

	return &RAGProxy{proxy: proxy}
}

// Handler возвращает базовый прокси-handler — main.go сам решает, какие префиксы
// открыть публично, а какие обернуть в RequireAdmin.
func (p *RAGProxy) Handler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		p.proxy.ServeHTTP(w, r)
	})
}

// RegisterPublicRoutes ставит на mux маршруты, доступные любому залогиненному юзеру:
// поиск и health.
func (p *RAGProxy) RegisterPublicRoutes(mux *http.ServeMux) {
	h := p.Handler()
	mux.Handle("/api/rag/search", h)
	mux.Handle("/api/rag/health", h)
}

// RegisterAdminRoutes ставит admin-only маршруты: ingest и управление документами.
// Вызывающий должен обернуть handler в admin-middleware.
// Префиксы с trailing slash покрывают sub-paths (например /ingest/upload, /documents/{id}).
func (p *RAGProxy) RegisterAdminRoutes(mux *http.ServeMux, wrap func(http.Handler) http.Handler) {
	h := wrap(p.Handler())
	mux.Handle("/api/rag/ingest", h)
	mux.Handle("/api/rag/ingest/", h)
	mux.Handle("/api/rag/documents", h)
	mux.Handle("/api/rag/documents/", h)
}
