package orchestrator

import (
	"encoding/json"
	"log"
	"net/http"
	"strings"

	"github.com/google/uuid"

	billinguc "legalbot/services/internal/billing/usecase"
	chatuc "legalbot/services/internal/chat/usecase"
	"legalbot/services/internal/middleware"
	"legalbot/services/internal/ragclient"
)

type AskHandler struct {
	ragClient      *ragclient.Client
	checkLimits    *billinguc.CheckLimitsUseCase
	recordUsage    *billinguc.RecordUsageUseCase
	createConv     *chatuc.CreateConversationUseCase
	saveMessage    *chatuc.SaveMessageUseCase
}

func NewAskHandler(
	ragClient *ragclient.Client,
	checkLimits *billinguc.CheckLimitsUseCase,
	recordUsage *billinguc.RecordUsageUseCase,
	createConv *chatuc.CreateConversationUseCase,
	saveMessage *chatuc.SaveMessageUseCase,
) *AskHandler {
	return &AskHandler{
		ragClient:   ragClient,
		checkLimits: checkLimits,
		recordUsage: recordUsage,
		createConv:  createConv,
		saveMessage: saveMessage,
	}
}

func (h *AskHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/chat/ask", h.handleAsk)
}

type askRequest struct {
	Query          string `json:"query"`
	TopK           int    `json:"top_k"`
	ConversationID string `json:"conversation_id,omitempty"`
}

type askResponse struct {
	Answer         string               `json:"answer"`
	Citations      []ragclient.Citation  `json:"citations"`
	Confidence     float64              `json:"confidence"`
	Provider       string               `json:"provider"`
	Model          string               `json:"model"`
	ConversationID string               `json:"conversation_id"`
	MessageID      string               `json:"message_id"`
}

func (h *AskHandler) handleAsk(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	ctx := r.Context()

	var req askRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if req.Query == "" {
		http.Error(w, "query is required", http.StatusBadRequest)
		return
	}
	if req.TopK <= 0 {
		req.TopK = 8
	}

	// 1. Extract userID from auth context (optional — works without auth too)
	userID, hasUser := middleware.GetUserID(ctx)
	var userUUID uuid.UUID
	if hasUser {
		parsed, err := uuid.Parse(userID)
		if err != nil {
			http.Error(w, "invalid user ID in token", http.StatusUnauthorized)
			return
		}
		userUUID = parsed
	}

	// 2. Check billing limits (skip if no subscription — MVP free tier)
	if hasUser {
		limitsResp, err := h.checkLimits.Execute(ctx, billinguc.CheckLimitsRequest{
			UserID:       userUUID,
			ResourceType: "requests",
			Amount:       1,
		})
		if err != nil {
			log.Printf("[ask] check_limits error: %v", err)
		} else if !limitsResp.Allowed && limitsResp.Reason != "no active subscription" {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusPaymentRequired)
			json.NewEncoder(w).Encode(map[string]interface{}{
				"error":  "limit exceeded",
				"reason": limitsResp.Reason,
				"used":   limitsResp.Used,
				"limit":  limitsResp.Limit,
			})
			return
		}
	}

	// 3. Create or reuse conversation
	var conversationID uuid.UUID
	if req.ConversationID != "" {
		parsed, err := uuid.Parse(req.ConversationID)
		if err != nil {
			http.Error(w, "invalid conversation_id", http.StatusBadRequest)
			return
		}
		conversationID = parsed
	} else if hasUser {
		convResp, err := h.createConv.Execute(ctx, chatuc.CreateConversationRequest{
			UserID: userUUID,
			Title:  truncate(req.Query, 100),
		})
		if err != nil {
			log.Printf("[ask] create_conversation error: %v", err)
		} else {
			conversationID = convResp.ConversationID
		}
	}

	// 4. Save user message
	if conversationID != uuid.Nil {
		_, err := h.saveMessage.Execute(ctx, chatuc.SaveMessageRequest{
			ConversationID: conversationID,
			Role:           "user",
			Content:        req.Query,
		})
		if err != nil {
			log.Printf("[ask] save user message error: %v", err)
		}
	}

	// 5. Call Python RAG /answer
	const noDocsAnswer = "В базе знаний пока нет документов. Добавьте документы через /api/rag/ingest, чтобы я мог отвечать на вопросы."
	ragResp, err := h.ragClient.Answer(ctx, req.Query, req.TopK)
	if err != nil {
		if strings.Contains(err.Error(), "404") {
			ragResp = &ragclient.AnswerResponse{
				Answer:   noDocsAnswer,
				Provider: "system",
				Model:    "none",
			}
		} else {
			http.Error(w, "RAG service error: "+err.Error(), http.StatusBadGateway)
			return
		}
	}

	// 6. Save assistant message with citations
	var messageID uuid.UUID
	if conversationID != uuid.Nil {
		citations := make([]chatuc.CitationData, 0, len(ragResp.Citations))
		for _, c := range ragResp.Citations {
			citations = append(citations, chatuc.CitationData{
				ChunkID:  c.ID,
				SourceID: c.ID,
				Score:    c.Score,
				Quote:    c.Quote,
				Meta:     c.Meta,
			})
		}

		msgResp, err := h.saveMessage.Execute(ctx, chatuc.SaveMessageRequest{
			ConversationID: conversationID,
			Role:           "assistant",
			Content:        ragResp.Answer,
			Metadata: map[string]interface{}{
				"provider":   ragResp.Provider,
				"model":      ragResp.Model,
				"confidence": ragResp.Confidence,
			},
			Citations: citations,
		})
		if err != nil {
			log.Printf("[ask] save assistant message error: %v", err)
		} else {
			messageID = msgResp.MessageID
		}
	}

	// 7. Record usage
	if hasUser {
		err := h.recordUsage.Execute(ctx, billinguc.RecordUsageRequest{
			UserID:       userUUID,
			ResourceType: "requests",
			Amount:       1,
		})
		if err != nil {
			log.Printf("[ask] record_usage error: %v", err)
		}
	}

	// 8. Return response
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
		Citations:      ragResp.Citations,
		Confidence:     ragResp.Confidence,
		Provider:       ragResp.Provider,
		Model:          ragResp.Model,
		ConversationID: convID,
		MessageID:      msgID,
	})
}

func truncate(s string, maxLen int) string {
	runes := []rune(s)
	if len(runes) <= maxLen {
		return s
	}
	return string(runes[:maxLen]) + "..."
}
