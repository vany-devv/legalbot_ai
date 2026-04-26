package orchestrator

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"

	"github.com/google/uuid"

	authdomain "legalbot/services/internal/auth/domain"
	authuc "legalbot/services/internal/auth/usecase"
	billinguc "legalbot/services/internal/billing/usecase"
	chatuc "legalbot/services/internal/chat/usecase"
	"legalbot/services/internal/middleware"
	"legalbot/services/internal/ragclient"
)

type AskHandler struct {
	ragClient   *ragclient.Client
	checkLimits *billinguc.CheckLimitsUseCase
	recordUsage *billinguc.RecordUsageUseCase
	createConv  *chatuc.CreateConversationUseCase
	saveMessage *chatuc.SaveMessageUseCase
	userRepo    authdomain.UserRepository
}

func NewAskHandler(
	ragClient *ragclient.Client,
	checkLimits *billinguc.CheckLimitsUseCase,
	recordUsage *billinguc.RecordUsageUseCase,
	createConv *chatuc.CreateConversationUseCase,
	saveMessage *chatuc.SaveMessageUseCase,
	userRepo authdomain.UserRepository,
) *AskHandler {
	return &AskHandler{
		ragClient:   ragClient,
		checkLimits: checkLimits,
		recordUsage: recordUsage,
		createConv:  createConv,
		saveMessage: saveMessage,
		userRepo:    userRepo,
	}
}

func (h *AskHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/chat/ask", h.handleAsk)
	mux.HandleFunc("/api/chat/ask/stream", h.handleAskStream)
}

type askRequest struct {
	Query          string `json:"query"`
	TopK           int    `json:"top_k"`
	ConversationID string `json:"conversation_id,omitempty"`
}

type citationResp struct {
	ID    string                 `json:"id"`
	Score float64                `json:"score"`
	Meta  map[string]interface{} `json:"meta"`
	Quote string                 `json:"quote"`
}

type askResponse struct {
	Answer         string         `json:"answer"`
	Citations      []citationResp `json:"citations"`
	Confidence     float64        `json:"confidence"`
	Provider       string         `json:"provider"`
	Model          string         `json:"model"`
	ConversationID string         `json:"conversation_id"`
	MessageID      string         `json:"message_id"`
}

// helpers

func writeSSE(w http.ResponseWriter, f http.Flusher, v any) {
	b, _ := json.Marshal(v)
	fmt.Fprintf(w, "data: %s\n\n", b)
	f.Flush()
}

func toCitationResps(cits []ragclient.Citation) []citationResp {
	out := make([]citationResp, 0, len(cits))
	for _, c := range cits {
		out = append(out, citationResp{ID: c.ID, Score: c.Score, Meta: c.Meta, Quote: c.Quote})
	}
	return out
}

// checkBilling возвращает true если запрос можно пропустить (в пределах лимита либо admin).
// Лениво проверяет admin-роль только когда лимит исчерпан — обычные юзеры в пределах
// лимита не делают лишнего FindByID.
func (h *AskHandler) checkBilling(r *http.Request, userUUID uuid.UUID) bool {
	limitsResp, err := h.checkLimits.Execute(r.Context(), billinguc.CheckLimitsRequest{
		UserID:       userUUID,
		ResourceType: "requests",
		Amount:       1,
	})
	if err != nil {
		log.Printf("[ask] check_limits error: %v", err)
		return true
	}
	if limitsResp.Allowed {
		return true
	}
	// Лимит не позволяет — последний шанс для админа
	return authuc.IsAdmin(r.Context(), h.userRepo, userUUID)
}

func (h *AskHandler) ensureConversation(r *http.Request, userUUID uuid.UUID, query, convIDStr string) uuid.UUID {
	if convIDStr != "" {
		if parsed, err := uuid.Parse(convIDStr); err == nil {
			return parsed
		}
	}
	convResp, err := h.createConv.Execute(r.Context(), chatuc.CreateConversationRequest{
		UserID: userUUID,
		Title:  truncate(query, 100),
	})
	if err != nil {
		log.Printf("[ask] create_conversation error: %v", err)
		return uuid.Nil
	}
	return convResp.ConversationID
}

func (h *AskHandler) saveUserMessage(r *http.Request, convID uuid.UUID, query string) {
	if convID == uuid.Nil {
		return
	}
	if _, err := h.saveMessage.Execute(r.Context(), chatuc.SaveMessageRequest{
		ConversationID: convID,
		Role:           "user",
		Content:        query,
	}); err != nil {
		log.Printf("[ask] save user message error: %v", err)
	}
}

func (h *AskHandler) recordUsageSafe(r *http.Request, userUUID uuid.UUID) {
	if err := h.recordUsage.Execute(r.Context(), billinguc.RecordUsageRequest{
		UserID:       userUUID,
		ResourceType: "requests",
		Amount:       1,
	}); err != nil {
		log.Printf("[ask] record_usage error: %v", err)
	}
}

// /api/chat/ask (non-streaming)

func (h *AskHandler) handleAsk(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	ctx := r.Context()

	var req askRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Query == "" {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if req.TopK <= 0 {
		req.TopK = 8
	}

	userID, hasUser := middleware.GetUserID(ctx)
	var userUUID uuid.UUID
	if hasUser {
		parsed, err := uuid.Parse(userID)
		if err != nil {
			http.Error(w, "invalid user ID in token", http.StatusUnauthorized)
			return
		}
		userUUID = parsed
		if !h.checkBilling(r, userUUID) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusPaymentRequired)
			json.NewEncoder(w).Encode(map[string]string{"error": "limit exceeded"})
			return
		}
	}

	var conversationID uuid.UUID
	if hasUser {
		conversationID = h.ensureConversation(r, userUUID, req.Query, req.ConversationID)
		h.saveUserMessage(r, conversationID, req.Query)
	}

	const noDocsAnswer = "В базе знаний пока нет документов. Добавьте документы через /api/rag/ingest, чтобы я мог отвечать на вопросы."
	ragResp, err := h.ragClient.Answer(ctx, req.Query, req.TopK)
	if err != nil {
		if strings.Contains(err.Error(), "404") {
			ragResp = &ragclient.AnswerResponse{Answer: noDocsAnswer, Provider: "system", Model: "none"}
		} else {
			http.Error(w, "RAG service error: "+err.Error(), http.StatusBadGateway)
			return
		}
	}

	var messageID uuid.UUID
	if conversationID != uuid.Nil {
		citData := make([]chatuc.CitationData, 0, len(ragResp.Citations))
		for _, c := range ragResp.Citations {
			citData = append(citData, chatuc.CitationData{ChunkID: c.ID, SourceID: c.ID, Score: c.Score, Quote: c.Quote, Meta: c.Meta})
		}
		msgResp, err := h.saveMessage.Execute(ctx, chatuc.SaveMessageRequest{
			ConversationID: conversationID,
			Role:           "assistant",
			Content:        ragResp.Answer,
			Metadata:       map[string]interface{}{"provider": ragResp.Provider, "model": ragResp.Model, "confidence": ragResp.Confidence},
			Citations:      citData,
		})
		if err != nil {
			log.Printf("[ask] save assistant message error: %v", err)
		} else {
			messageID = msgResp.MessageID
		}
	}

	if hasUser {
		h.recordUsageSafe(r, userUUID)
	}

	convID := ""
	if conversationID != uuid.Nil {
		convID = conversationID.String()
	}
	msgID := ""
	if messageID != uuid.Nil {
		msgID = messageID.String()
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(askResponse{
		Answer:         ragResp.Answer,
		Citations:      toCitationResps(ragResp.Citations),
		Confidence:     ragResp.Confidence,
		Provider:       ragResp.Provider,
		Model:          ragResp.Model,
		ConversationID: convID,
		MessageID:      msgID,
	})
}

// /api/chat/ask/stream (SSE)

func (h *AskHandler) handleAskStream(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	ctx := r.Context()

	var req askRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Query == "" {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if req.TopK <= 0 {
		req.TopK = 8
	}

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming not supported", http.StatusInternalServerError)
		return
	}

	userID, hasUser := middleware.GetUserID(ctx)
	var userUUID uuid.UUID
	if hasUser {
		parsed, err := uuid.Parse(userID)
		if err != nil {
			http.Error(w, "invalid user ID in token", http.StatusUnauthorized)
			return
		}
		userUUID = parsed
		if !h.checkBilling(r, userUUID) {
			http.Error(w, "limit exceeded", http.StatusPaymentRequired)
			return
		}
	}

	var conversationID uuid.UUID
	if hasUser {
		conversationID = h.ensureConversation(r, userUUID, req.Query, req.ConversationID)
		h.saveUserMessage(r, conversationID, req.Query)
	}

	// SSE headers — must be set before first write
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("X-Accel-Buffering", "no")

	// Stage 1
	writeSSE(w, flusher, map[string]any{"type": "thinking", "text": "Поиск в базе знаний..."})

	ragStream, err := h.ragClient.AnswerStream(ctx, req.Query, req.TopK)
	if err != nil {
		writeSSE(w, flusher, map[string]any{"type": "error", "text": err.Error()})
		fmt.Fprintf(w, "data: [DONE]\n\n")
		flusher.Flush()
		return
	}
	defer ragStream.Body.Close()

	var fullContent strings.Builder
	var citations []ragclient.Citation
	firstDelta := true

	scanner := bufio.NewScanner(ragStream.Body)
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

		switch event.Type {
		case "citations":
			var cits []ragclient.Citation
			if err := json.Unmarshal(event.Data, &cits); err == nil {
				citations = cits
			}
			writeSSE(w, flusher, map[string]any{"type": "citations", "data": toCitationResps(citations)})

		case "delta":
			var delta string
			if err := json.Unmarshal(event.Data, &delta); err == nil && delta != "" {
				if firstDelta {
					writeSSE(w, flusher, map[string]any{"type": "thinking", "text": "Анализирую источники и формирую ответ..."})
					firstDelta = false
				}
				fullContent.WriteString(delta)
				writeSSE(w, flusher, map[string]any{"type": "delta", "data": delta})
			}
		}
	}

	// Save to DB
	convID := ""
	msgID := ""
	if conversationID != uuid.Nil {
		citData := make([]chatuc.CitationData, 0, len(citations))
		for _, c := range citations {
			citData = append(citData, chatuc.CitationData{ChunkID: c.ID, SourceID: c.ID, Score: c.Score, Quote: c.Quote, Meta: c.Meta})
		}
		msgResp, err := h.saveMessage.Execute(ctx, chatuc.SaveMessageRequest{
			ConversationID: conversationID,
			Role:           "assistant",
			Content:        fullContent.String(),
			Metadata:       map[string]interface{}{"provider": "gigachat", "model": "GigaChat-Pro"},
			Citations:      citData,
		})
		if err != nil {
			log.Printf("[ask/stream] save assistant message error: %v", err)
		} else {
			msgID = msgResp.MessageID.String()
		}
		convID = conversationID.String()
	}

	if hasUser {
		h.recordUsageSafe(r, userUUID)
	}

	writeSSE(w, flusher, map[string]any{
		"type":            "done",
		"conversation_id": convID,
		"message_id":      msgID,
	})
	fmt.Fprintf(w, "data: [DONE]\n\n")
	flusher.Flush()
}

func truncate(s string, maxLen int) string {
	runes := []rune(s)
	if len(runes) <= maxLen {
		return s
	}
	return string(runes[:maxLen]) + "..."
}
