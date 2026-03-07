package ragclient

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

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
	ID    string                 `json:"id"`
	Score float64                `json:"score"`
	Meta  map[string]interface{} `json:"meta"`
	Quote string                 `json:"quote"`
}

type AnswerResponse struct {
	Answer     string     `json:"answer"`
	Citations  []Citation `json:"citations"`
	Confidence float64    `json:"confidence"`
	UsedChunks []string   `json:"used_chunks"`
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

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("call RAG service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("RAG service returned %d: %s", resp.StatusCode, string(body))
	}

	var result AnswerResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("decode RAG response: %w", err)
	}

	return &result, nil
}

func (c *Client) Health(ctx context.Context) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+"/health", nil)
	if err != nil {
		return fmt.Errorf("create request: %w", err)
	}

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
