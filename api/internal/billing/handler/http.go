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
	mux.HandleFunc("/api/billing/me", h.handleMe)
}

func (h *BillingHandler) handleCreateSubscription(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	userID, ok := currentBillingUserID(r)
	if !ok {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	var req usecase.CreateSubscriptionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	req.UserID = userID

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
	userID, ok := currentBillingUserID(r)
	if !ok {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	var req usecase.CheckLimitsRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	req.UserID = userID

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
	userID, ok := currentBillingUserID(r)
	if !ok {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	var req usecase.RecordUsageRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	req.UserID = userID

	if err := h.recordUsageUC.Execute(r.Context(), req); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func currentBillingUserID(r *http.Request) (uuid.UUID, bool) {
	userIDStr, ok := middleware.GetUserID(r.Context())
	if !ok || userIDStr == "" {
		return uuid.Nil, false
	}
	userID, err := uuid.Parse(userIDStr)
	if err != nil {
		return uuid.Nil, false
	}
	return userID, true
}
