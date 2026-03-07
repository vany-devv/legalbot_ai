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

func NewRAGProxy(rawURL string) *RAGProxy {
	target, _ := url.Parse(rawURL)

	proxy := httputil.NewSingleHostReverseProxy(target)

	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalDirector(req)
		req.URL.Path = strings.TrimPrefix(req.URL.Path, "/api/rag")
		req.Host = target.Host
	}

	return &RAGProxy{proxy: proxy}
}

func (p *RAGProxy) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/rag/", p.handle)
}

func (p *RAGProxy) handle(w http.ResponseWriter, r *http.Request) {
	p.proxy.ServeHTTP(w, r)
}
