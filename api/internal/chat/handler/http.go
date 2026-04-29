package handler

import (
	"encoding/json"
	"errors"
	"net/http"
	"strings"

	"github.com/google/uuid"
	"legalbot/services/internal/chat/usecase"
	"legalbot/services/internal/middleware"
)

type ChatHandler struct {
	createConversationUC *usecase.CreateConversationUseCase
	saveMessageUC        *usecase.SaveMessageUseCase
	getConversationUC    *usecase.GetConversationUseCase
	listConversationsUC  *usecase.ListConversationsUseCase
}

func NewChatHandler(
	createConversationUC *usecase.CreateConversationUseCase,
	saveMessageUC *usecase.SaveMessageUseCase,
	getConversationUC *usecase.GetConversationUseCase,
	listConversationsUC *usecase.ListConversationsUseCase,
) *ChatHandler {
	return &ChatHandler{
		createConversationUC: createConversationUC,
		saveMessageUC:        saveMessageUC,
		getConversationUC:    getConversationUC,
		listConversationsUC:  listConversationsUC,
	}
}

func (h *ChatHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/chat/conversations", h.handleConversations)
	mux.HandleFunc("/api/chat/messages", h.handleSaveMessage)
	mux.HandleFunc("/api/chat/conversations/", h.handleGetConversation)
}

func (h *ChatHandler) handleConversations(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		h.handleListConversations(w, r)
	case http.MethodPost:
		h.handleCreateConversation(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func (h *ChatHandler) handleListConversations(w http.ResponseWriter, r *http.Request) {
	userID, ok := middleware.GetUserID(r.Context())
	if !ok {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	parsed, err := uuid.Parse(userID)
	if err != nil {
		http.Error(w, "Invalid user ID", http.StatusBadRequest)
		return
	}

	resp, err := h.listConversationsUC.Execute(r.Context(), parsed, 50, 0)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *ChatHandler) handleCreateConversation(w http.ResponseWriter, r *http.Request) {
	userID, ok := currentUserID(r)
	if !ok {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var req usecase.CreateConversationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	req.UserID = userID

	resp, err := h.createConversationUC.Execute(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *ChatHandler) handleSaveMessage(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	userID, ok := currentUserID(r)
	if !ok {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	var req usecase.SaveMessageRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	req.UserID = userID

	resp, err := h.saveMessageUC.Execute(r.Context(), req)
	if err != nil {
		switch {
		case errors.Is(err, usecase.ErrConversationForbidden):
			http.Error(w, err.Error(), http.StatusForbidden)
		case errors.Is(err, usecase.ErrConversationNotFound):
			http.Error(w, err.Error(), http.StatusNotFound)
		default:
			http.Error(w, err.Error(), http.StatusBadRequest)
		}
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
	userID, ok := currentUserID(r)
	if !ok {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	path := strings.TrimPrefix(r.URL.Path, "/api/chat/conversations/")
	idStr := strings.Split(path, "/")[0]
	conversationID, err := uuid.Parse(idStr)
	if err != nil {
		http.Error(w, "Invalid conversation ID", http.StatusBadRequest)
		return
	}

	resp, err := h.getConversationUC.Execute(r.Context(), conversationID, userID)
	if err != nil {
		switch {
		case errors.Is(err, usecase.ErrConversationForbidden):
			http.Error(w, err.Error(), http.StatusForbidden)
		case errors.Is(err, usecase.ErrConversationNotFound):
			http.Error(w, err.Error(), http.StatusNotFound)
		default:
			http.Error(w, err.Error(), http.StatusInternalServerError)
		}
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func currentUserID(r *http.Request) (uuid.UUID, bool) {
	userID, ok := middleware.GetUserID(r.Context())
	if !ok || userID == "" {
		return uuid.Nil, false
	}
	parsed, err := uuid.Parse(userID)
	if err != nil {
		return uuid.Nil, false
	}
	return parsed, true
}
