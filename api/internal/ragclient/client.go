package ragclient

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"time"

	"legalbot/services/internal/pkg/logger"
)

const requestIDHeader = "X-Request-ID"

// setRequestID копирует X-Request-ID из контекста в исходящий запрос —
// чтобы в логах RAG-сервиса можно было найти ту же операцию по тому же id.
func setRequestID(ctx context.Context, req *http.Request) {
	if rid := logger.RequestID(ctx); rid != "" {
		req.Header.Set(requestIDHeader, rid)
	}
}

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}

type Client struct {
	baseURL    string
	httpClient *http.Client
}

func New(baseURL string) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 90 * time.Second,
		},
	}
}

type AnswerRequest struct {
	Query     string `json:"query"`
	TopK      int    `json:"top_k"`
	MaxTokens int    `json:"max_tokens,omitempty"`
}

type Citation struct {
	ID    string                 `json:"chunk_id"`
	Score float64                `json:"retrieval_score"`
	Meta  map[string]interface{} `json:"meta"`
	Quote string                 `json:"content"`
}

type AnswerResponse struct {
	Answer     string     `json:"answer"`
	Citations  []Citation `json:"citations"`
	Confidence float64    `json:"confidence"`
	Provider   string     `json:"provider"`
	Model      string     `json:"model"`
}

func (c *Client) Answer(ctx context.Context, query string, topK int) (*AnswerResponse, error) {
	reqBody := AnswerRequest{
		Query: query,
		TopK:  topK,
	}

	bodyBytes, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/answer", bytes.NewReader(bodyBytes))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	setRequestID(ctx, req)

	log := logger.FromCtx(ctx)
	start := time.Now()

	resp, err := c.httpClient.Do(req)
	if err != nil {
		log.Error("rag_call_failed", "endpoint", "/answer", "err", err)
		return nil, fmt.Errorf("call RAG service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		log.Error("rag_call_failed", "endpoint", "/answer", "status", resp.StatusCode, "body", truncate(string(body), 256))
		return nil, fmt.Errorf("RAG service returned %d: %s", resp.StatusCode, string(body))
	}

	var result AnswerResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode RAG response: %w", err)
	}

	log.Info("rag_call",
		"endpoint", "/answer",
		"status", resp.StatusCode,
		"duration_ms", time.Since(start).Milliseconds(),
		"top_k", topK,
		"citations", len(result.Citations),
		"provider", result.Provider,
		"model", result.Model,
	)
	return &result, nil
}

// AnswerStream calls POST /answer/stream and returns the raw SSE response.
// The caller is responsible for closing resp.Body.
func (c *Client) AnswerStream(ctx context.Context, query string, topK int) (*http.Response, error) {
	reqBody := AnswerRequest{Query: query, TopK: topK}
	bodyBytes, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		c.baseURL+"/answer/stream", bytes.NewReader(bodyBytes))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")
	setRequestID(ctx, req)

	log := logger.FromCtx(ctx)

	// No timeout for streaming
	resp, err := (&http.Client{}).Do(req)
	if err != nil {
		log.Error("rag_call_failed", "endpoint", "/answer/stream", "err", err)
		return nil, fmt.Errorf("call RAG stream: %w", err)
	}
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		log.Error("rag_call_failed", "endpoint", "/answer/stream", "status", resp.StatusCode, "body", truncate(string(body), 256))
		return nil, fmt.Errorf("RAG service returned %d: %s", resp.StatusCode, string(body))
	}
	log.Info("rag_call", "endpoint", "/answer/stream", "status", resp.StatusCode, "top_k", topK)
	return resp, nil
}

// AnalyzeStream sends ad text (and optionally a file) to POST /analyze/stream
// as multipart/form-data and returns the raw SSE response.
func (c *Client) AnalyzeStream(ctx context.Context, text string, fileData io.Reader, filename string, topK int) (*http.Response, error) {
	pr, pw := io.Pipe()
	w := multipart.NewWriter(pw)
	contentType := w.FormDataContentType()

	go func() {
		defer pw.Close()
		defer w.Close()

		if text != "" {
			if err := w.WriteField("text", text); err != nil {
				_ = pw.CloseWithError(fmt.Errorf("write text field: %w", err))
				return
			}
		}
		if fileData != nil && filename != "" {
			part, err := w.CreateFormFile("file", filename)
			if err != nil {
				_ = pw.CloseWithError(fmt.Errorf("create form file: %w", err))
				return
			}
			if _, err := io.Copy(part, fileData); err != nil {
				_ = pw.CloseWithError(fmt.Errorf("copy file data: %w", err))
				return
			}
		}
		if err := w.WriteField("top_k", fmt.Sprintf("%d", topK)); err != nil {
			_ = pw.CloseWithError(fmt.Errorf("write top_k field: %w", err))
			return
		}
	}()

	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		c.baseURL+"/analyze/stream", pr)
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", contentType)
	req.Header.Set("Accept", "text/event-stream")
	setRequestID(ctx, req)

	log := logger.FromCtx(ctx)

	resp, err := (&http.Client{}).Do(req)
	if err != nil {
		log.Error("rag_call_failed", "endpoint", "/analyze/stream", "err", err)
		return nil, fmt.Errorf("call RAG analyze stream: %w", err)
	}
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		log.Error("rag_call_failed", "endpoint", "/analyze/stream", "status", resp.StatusCode, "body", truncate(string(body), 256))
		return nil, fmt.Errorf("RAG analyze returned %d: %s", resp.StatusCode, string(body))
	}
	log.Info("rag_call", "endpoint", "/analyze/stream", "status", resp.StatusCode, "top_k", topK, "has_file", filename != "")
	return resp, nil
}

// GenerateReport отправляет JSON сохранённого анализа в POST /report/pdf и
// возвращает сырой ответ (application/pdf). Вызывающий обязан закрыть Body.
func (c *Client) GenerateReport(ctx context.Context, payload []byte) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		c.baseURL+"/report/pdf", bytes.NewReader(payload))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/pdf")
	setRequestID(ctx, req)

	log := logger.FromCtx(ctx)
	resp, err := c.httpClient.Do(req)
	if err != nil {
		log.Error("rag_call_failed", "endpoint", "/report/pdf", "err", err)
		return nil, fmt.Errorf("call RAG report: %w", err)
	}
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		log.Error("rag_call_failed", "endpoint", "/report/pdf", "status", resp.StatusCode, "body", truncate(string(body), 256))
		return nil, fmt.Errorf("RAG report returned %d: %s", resp.StatusCode, string(body))
	}
	log.Info("rag_call", "endpoint", "/report/pdf", "status", resp.StatusCode)
	return resp, nil
}

func (c *Client) Health(ctx context.Context) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+"/health", nil)
	if err != nil {
		return fmt.Errorf("create request: %w", err)
	}
	setRequestID(ctx, req)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("call RAG health: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("RAG health returned %d", resp.StatusCode)
	}
	return nil
}
