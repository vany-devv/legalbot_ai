package orchestrator

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"

	"github.com/google/uuid"

	analysisuc "legalbot/services/internal/analysis/usecase"
	authdomain "legalbot/services/internal/auth/domain"
	authuc "legalbot/services/internal/auth/usecase"
	billinguc "legalbot/services/internal/billing/usecase"
	"legalbot/services/internal/middleware"
	"legalbot/services/internal/ragclient"
)

const analyzeMaxUploadBytes int64 = 32 << 20

type AnalyzeHandler struct {
	ragClient   *ragclient.Client
	checkLimits *billinguc.CheckLimitsUseCase
	recordUsage *billinguc.RecordUsageUseCase
	userRepo    authdomain.UserRepository
	saveAnalys  *analysisuc.SaveAnalysisUseCase
}

func NewAnalyzeHandler(
	ragClient *ragclient.Client,
	checkLimits *billinguc.CheckLimitsUseCase,
	recordUsage *billinguc.RecordUsageUseCase,
	userRepo authdomain.UserRepository,
	saveAnalys *analysisuc.SaveAnalysisUseCase,
) *AnalyzeHandler {
	return &AnalyzeHandler{
		ragClient:   ragClient,
		checkLimits: checkLimits,
		recordUsage: recordUsage,
		userRepo:    userRepo,
		saveAnalys:  saveAnalys,
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
	var parsedUserID uuid.UUID
	if hasUser {
		parsed, err := uuid.Parse(userID)
		if err != nil {
			http.Error(w, "invalid user ID in token", http.StatusUnauthorized)
			return
		}
		parsedUserID = parsed
		limitsResp, err := h.checkLimits.Execute(ctx, billinguc.CheckLimitsRequest{
			UserID:       parsed,
			ResourceType: "requests",
			Amount:       1,
		})
		if err != nil {
			log.Printf("[analyze] check_limits error: %v", err)
		} else if !limitsResp.Allowed {
			if !authuc.IsAdmin(ctx, h.userRepo, parsed) {
				http.Error(w, "limit exceeded", http.StatusPaymentRequired)
				return
			}
		}
	}

	r.Body = http.MaxBytesReader(w, r.Body, analyzeMaxUploadBytes)

	if err := r.ParseMultipartForm(32 << 20); err != nil {
		var maxBytesErr *http.MaxBytesError
		if errors.As(err, &maxBytesErr) {
			http.Error(w, "uploaded file is too large", http.StatusRequestEntityTooLarge)
			return
		}
		http.Error(w, "invalid multipart form", http.StatusBadRequest)
		return
	}
	if r.MultipartForm != nil {
		defer r.MultipartForm.RemoveAll()
	}

	text := r.FormValue("text")
	topK := r.FormValue("top_k")
	if topK == "" {
		topK = "10"
	}

	var fileData io.Reader
	var filename string
	file, header, err := r.FormFile("file")
	if err == nil {
		defer file.Close()
		fileData = file
		filename = header.Filename
	}

	if text == "" && fileData == nil {
		http.Error(w, "provide either 'text' or 'file'", http.StatusBadRequest)
		return
	}

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

	// Аккумулируем нужные события — для последующего сохранения в историю.
	var (
		capturedAdText    string
		capturedResult    json.RawMessage
		capturedCitations json.RawMessage
	)

	scanner := bufio.NewScanner(ragResp.Body)
	scanner.Buffer(make([]byte, 512*1024), 512*1024)
	streamCompleted := false

	for scanner.Scan() {
		line := scanner.Text()
		if !strings.HasPrefix(line, "data: ") {
			continue
		}
		payload := strings.TrimPrefix(line, "data: ")
		if payload == "[DONE]" {
			streamCompleted = true
			break
		}

		var event struct {
			Type string          `json:"type"`
			Data json.RawMessage `json:"data"`
			Text string          `json:"text"`
		}
		if err := json.Unmarshal([]byte(payload), &event); err != nil {
			continue
		}

		switch event.Type {
		case "ad_text":
			capturedAdText = event.Text
		case "result":
			capturedResult = append(capturedResult[:0], event.Data...)
		case "citations":
			capturedCitations = append(capturedCitations[:0], event.Data...)
		}

		writeSSE(w, flusher, json.RawMessage(payload))
	}
	if err := scanner.Err(); err != nil {
		writeSSE(w, flusher, map[string]any{"type": "error", "text": "stream read failed"})
		fmt.Fprintf(w, "data: [DONE]\n\n")
		flusher.Flush()
		return
	}

	// Save analysis & record usage только при успешном анализе.
	if streamCompleted {
		if hasUser {
			if err := h.recordUsage.Execute(ctx, billinguc.RecordUsageRequest{
				UserID:       parsedUserID,
				ResourceType: "requests",
				Amount:       1,
			}); err != nil {
				log.Printf("[analyze] record_usage error: %v", err)
			}

			// Persist в историю — только если есть и текст и результат.
			if h.saveAnalys != nil && capturedAdText != "" && len(capturedResult) > 0 {
				saved, err := h.saveAnalys.Execute(ctx, analysisuc.SaveRequest{
					UserID:    parsedUserID,
					AdText:    capturedAdText,
					Result:    capturedResult,
					Citations: capturedCitations,
				})
				if err != nil {
					log.Printf("[analyze] save history error: %v", err)
				} else {
					writeSSE(w, flusher, map[string]any{
						"type":  "saved",
						"id":    saved.ID.String(),
						"title": saved.Title,
					})
				}
			}
		}
	}

	writeSSE(w, flusher, map[string]any{"type": "done"})
	fmt.Fprintf(w, "data: [DONE]\n\n")
	flusher.Flush()
}
