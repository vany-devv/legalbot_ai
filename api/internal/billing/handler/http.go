package handler

import (
	"encoding/json"
	"net/http"

	"github.com/google/uuid"
	"legalbot/services/internal/billing/usecase"
	"legalbot/services/internal/middleware"
)

type BillingHandler struct {
	createSubscriptionUC *usecase.CreateSubscriptionUseCase
	checkLimitsUC        *usecase.CheckLimitsUseCase
	recordUsageUC        *usecase.RecordUsageUseCase
	getUserBillingUC     *usecase.GetUserBillingUseCase
}

func NewBillingHandler(
	createSubscriptionUC *usecase.CreateSubscriptionUseCase,
	checkLimitsUC *usecase.CheckLimitsUseCase,
	recordUsageUC *usecase.RecordUsageUseCase,
	getUserBillingUC *usecase.GetUserBillingUseCase,
) *BillingHandler {
	return &BillingHandler{
		createSubscriptionUC: createSubscriptionUC,
		checkLimitsUC:        checkLimitsUC,
		recordUsageUC:        recordUsageUC,
		getUserBillingUC:     getUserBillingUC,
	}
}

func (h *BillingHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/billing/subscriptions", h.handleCreateSubscription)
	mux.HandleFunc("/api/billing/limits/check", h.handleCheckLimits)
	mux.HandleFunc("/api/billing/usage", h.handleRecordUsage)
	mux.HandleFunc("/api/billing/me", h.handleMe)
}

func (h *BillingHandler) handleCreateSubscription(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req usecase.CreateSubscriptionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	resp, err := h.createSubscriptionUC.Execute(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *BillingHandler) handleCheckLimits(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req usecase.CheckLimitsRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	resp, err := h.checkLimitsUC.Execute(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *BillingHandler) handleMe(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	userIDStr, ok := middleware.GetUserID(r.Context())
	if !ok || userIDStr == "" {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	userID, err := uuid.Parse(userIDStr)
	if err != nil {
		http.Error(w, "invalid user id", http.StatusUnauthorized)
		return
	}

	resp, err := h.getUserBillingUC.Execute(r.Context(), userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *BillingHandler) handleRecordUsage(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req usecase.RecordUsageRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	if err := h.recordUsageUC.Execute(r.Context(), req); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
}
