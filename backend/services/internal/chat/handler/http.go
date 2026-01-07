package handler

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/google/uuid"
	"legalbot/services/internal/chat/usecase"
)

type ChatHandler struct {
	createConversationUC *usecase.CreateConversationUseCase
	saveMessageUC        *usecase.SaveMessageUseCase
	getConversationUC    *usecase.GetConversationUseCase
}

func NewChatHandler(
	createConversationUC *usecase.CreateConversationUseCase,
	saveMessageUC *usecase.SaveMessageUseCase,
	getConversationUC *usecase.GetConversationUseCase,
) *ChatHandler {
	return &ChatHandler{
		createConversationUC: createConversationUC,
		saveMessageUC:        saveMessageUC,
		getConversationUC:    getConversationUC,
	}
}

func (h *ChatHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("POST /api/chat/conversations", h.handleCreateConversation)
	mux.HandleFunc("POST /api/chat/messages", h.handleSaveMessage)
	mux.HandleFunc("/api/chat/conversations/", h.handleGetConversation)
}

func (h *ChatHandler) handleCreateConversation(w http.ResponseWriter, r *http.Request) {
	var req usecase.CreateConversationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	// TODO: извлечь userID из JWT токена
	// req.UserID = extractUserIDFromToken(r)

	resp, err := h.createConversationUC.Execute(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *ChatHandler) handleSaveMessage(w http.ResponseWriter, r *http.Request) {
	var req usecase.SaveMessageRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	resp, err := h.saveMessageUC.Execute(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *ChatHandler) handleGetConversation(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Парсинг ID из пути
	path := strings.TrimPrefix(r.URL.Path, "/api/chat/conversations/")
	idStr := strings.Split(path, "/")[0]
	conversationID, err := uuid.Parse(idStr)
	if err != nil {
		http.Error(w, "Invalid conversation ID", http.StatusBadRequest)
		return
	}

	resp, err := h.getConversationUC.Execute(r.Context(), conversationID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

