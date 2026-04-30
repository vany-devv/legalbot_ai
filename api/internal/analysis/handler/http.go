package handler

import (
	"encoding/json"
	"errors"
	"net/http"
	"strings"

	"github.com/google/uuid"
	"legalbot/services/internal/analysis/usecase"
	"legalbot/services/internal/middleware"
)

type AnalysisHandler struct {
	listUC   *usecase.ListAnalysesUseCase
	getUC    *usecase.GetAnalysisUseCase
	deleteUC *usecase.DeleteAnalysisUseCase
}

func NewAnalysisHandler(
	listUC *usecase.ListAnalysesUseCase,
	getUC *usecase.GetAnalysisUseCase,
	deleteUC *usecase.DeleteAnalysisUseCase,
) *AnalysisHandler {
	return &AnalysisHandler{listUC: listUC, getUC: getUC, deleteUC: deleteUC}
}

func (h *AnalysisHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/analyses", h.handleList)
	mux.HandleFunc("/api/analyses/", h.handleByID)
}

func (h *AnalysisHandler) handleList(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	userID, ok := currentUserID(r)
	if !ok {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	items, err := h.listUC.Execute(r.Context(), userID, 50, 0)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if items == nil {
		items = []usecase.ListItem{}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(items)
}

func (h *AnalysisHandler) handleByID(w http.ResponseWriter, r *http.Request) {
	userID, ok := currentUserID(r)
	if !ok {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}
	idStr := strings.TrimPrefix(r.URL.Path, "/api/analyses/")
	idStr = strings.Split(idStr, "/")[0]
	id, err := uuid.Parse(idStr)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		resp, err := h.getUC.Execute(r.Context(), id, userID)
		if err != nil {
			if errors.Is(err, usecase.ErrForbidden) {
				http.Error(w, err.Error(), http.StatusForbidden)
				return
			}
			http.Error(w, err.Error(), http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)

	case http.MethodDelete:
		if err := h.deleteUC.Execute(r.Context(), id, userID); err != nil {
			http.Error(w, err.Error(), http.StatusNotFound)
			return
		}
		w.WriteHeader(http.StatusNoContent)

	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
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
