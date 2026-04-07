package orchestrator

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"

	"github.com/google/uuid"

	billinguc "legalbot/services/internal/billing/usecase"
	"legalbot/services/internal/middleware"
	"legalbot/services/internal/ragclient"
)

type AnalyzeHandler struct {
	ragClient   *ragclient.Client
	checkLimits *billinguc.CheckLimitsUseCase
	recordUsage *billinguc.RecordUsageUseCase
}

func NewAnalyzeHandler(
	ragClient *ragclient.Client,
	checkLimits *billinguc.CheckLimitsUseCase,
	recordUsage *billinguc.RecordUsageUseCase,
) *AnalyzeHandler {
	return &AnalyzeHandler{
		ragClient:   ragClient,
		checkLimits: checkLimits,
		recordUsage: recordUsage,
	}
}

func (h *AnalyzeHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/analyze/stream", h.handleAnalyzeStream)
}

func (h *AnalyzeHandler) handleAnalyzeStream(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	ctx := r.Context()

	// Auth & billing
	userID, hasUser := middleware.GetUserID(ctx)
	if hasUser {
		parsed, err := uuid.Parse(userID)
		if err != nil {
			http.Error(w, "invalid user ID in token", http.StatusUnauthorized)
			return
		}
		limitsResp, err := h.checkLimits.Execute(ctx, billinguc.CheckLimitsRequest{
			UserID:       parsed,
			ResourceType: "requests",
			Amount:       1,
		})
		if err != nil {
			log.Printf("[analyze] check_limits error: %v", err)
		} else if !limitsResp.Allowed {
			http.Error(w, "limit exceeded", http.StatusPaymentRequired)
			return
		}
	}

	// Parse multipart from client
	if err := r.ParseMultipartForm(32 << 20); err != nil {
		http.Error(w, "invalid multipart form", http.StatusBadRequest)
		return
	}

	text := r.FormValue("text")
	topK := r.FormValue("top_k")
	if topK == "" {
		topK = "10"
	}

	// Read uploaded file if present
	var fileData io.Reader
	var filename string
	file, header, err := r.FormFile("file")
	if err == nil {
		defer file.Close()
		var buf bytes.Buffer
		io.Copy(&buf, file)
		fileData = &buf
		filename = header.Filename
	}

	if text == "" && fileData == nil {
		http.Error(w, "provide either 'text' or 'file'", http.StatusBadRequest)
		return
	}

	// SSE headers
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming not supported", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")

	writeSSE(w, flusher, map[string]any{"type": "thinking", "text": "Извлекаю текст и ищу релевантные нормы..."})

	// Forward to RAG /analyze/stream
	topKInt := 10
	fmt.Sscanf(topK, "%d", &topKInt)

	ragResp, err := h.ragClient.AnalyzeStream(ctx, text, fileData, filename, topKInt)
	if err != nil {
		writeSSE(w, flusher, map[string]any{"type": "error", "text": err.Error()})
		fmt.Fprintf(w, "data: [DONE]\n\n")
		flusher.Flush()
		return
	}
	defer ragResp.Body.Close()

	writeSSE(w, flusher, map[string]any{"type": "thinking", "text": "Анализирую рекламный материал..."})

	// Proxy SSE events from RAG to client
	scanner := bufio.NewScanner(ragResp.Body)
	scanner.Buffer(make([]byte, 512*1024), 512*1024)

	for scanner.Scan() {
		line := scanner.Text()
		if !strings.HasPrefix(line, "data: ") {
			continue
		}
		payload := strings.TrimPrefix(line, "data: ")
		if payload == "[DONE]" {
			break
		}

		var event struct {
			Type string          `json:"type"`
			Data json.RawMessage `json:"data"`
		}
		if err := json.Unmarshal([]byte(payload), &event); err != nil {
			continue
		}

		// Forward all events as-is
		writeSSE(w, flusher, json.RawMessage(payload))
	}

	// Record usage
	if hasUser {
		parsed, _ := uuid.Parse(userID)
		if err := h.recordUsage.Execute(ctx, billinguc.RecordUsageRequest{
			UserID:       parsed,
			ResourceType: "requests",
			Amount:       1,
		}); err != nil {
			log.Printf("[analyze] record_usage error: %v", err)
		}
	}

	writeSSE(w, flusher, map[string]any{"type": "done"})
	fmt.Fprintf(w, "data: [DONE]\n\n")
	flusher.Flush()
}
