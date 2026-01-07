package handler

import (
	"encoding/json"
	"net/http"

	"github.com/google/uuid"
	"legalbot/services/internal/billing/usecase"
)

type BillingHandler struct {
	createSubscriptionUC *usecase.CreateSubscriptionUseCase
	checkLimitsUC        *usecase.CheckLimitsUseCase
	recordUsageUC        *usecase.RecordUsageUseCase
}

func NewBillingHandler(
	createSubscriptionUC *usecase.CreateSubscriptionUseCase,
	checkLimitsUC *usecase.CheckLimitsUseCase,
	recordUsageUC *usecase.RecordUsageUseCase,
) *BillingHandler {
	return &BillingHandler{
		createSubscriptionUC: createSubscriptionUC,
		checkLimitsUC:        checkLimitsUC,
		recordUsageUC:        recordUsageUC,
	}
}

func (h *BillingHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("POST /api/billing/subscriptions", h.handleCreateSubscription)
	mux.HandleFunc("POST /api/billing/limits/check", h.handleCheckLimits)
	mux.HandleFunc("POST /api/billing/usage", h.handleRecordUsage)
}

func (h *BillingHandler) handleCreateSubscription(w http.ResponseWriter, r *http.Request) {
	var req usecase.CreateSubscriptionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	// TODO: извлечь userID из JWT токена
	// req.UserID = extractUserIDFromToken(r)

	resp, err := h.createSubscriptionUC.Execute(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *BillingHandler) handleCheckLimits(w http.ResponseWriter, r *http.Request) {
	var req usecase.CheckLimitsRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	// TODO: извлечь userID из JWT токена

	resp, err := h.checkLimitsUC.Execute(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *BillingHandler) handleRecordUsage(w http.ResponseWriter, r *http.Request) {
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






