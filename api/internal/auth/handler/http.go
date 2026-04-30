package handler

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/google/uuid"
	"legalbot/services/internal/auth/usecase"
	"legalbot/services/internal/middleware"
)

type AuthHandler struct {
	registerUseCase          *usecase.RegisterUseCase
	loginUseCase             *usecase.LoginUseCase
	getMeUseCase             *usecase.GetMeUseCase
	changePasswordUseCase    *usecase.ChangePasswordUseCase
	logoutUseCase            *usecase.LogoutUseCase
	updatePreferencesUseCase *usecase.UpdatePreferencesUseCase
}

func NewAuthHandler(
	registerUseCase *usecase.RegisterUseCase,
	loginUseCase *usecase.LoginUseCase,
	getMeUseCase *usecase.GetMeUseCase,
	changePasswordUseCase *usecase.ChangePasswordUseCase,
	logoutUseCase *usecase.LogoutUseCase,
	updatePreferencesUseCase *usecase.UpdatePreferencesUseCase,
) *AuthHandler {
	return &AuthHandler{
		registerUseCase:          registerUseCase,
		loginUseCase:             loginUseCase,
		getMeUseCase:             getMeUseCase,
		changePasswordUseCase:    changePasswordUseCase,
		logoutUseCase:            logoutUseCase,
		updatePreferencesUseCase: updatePreferencesUseCase,
	}
}

func (h *AuthHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/auth/register", h.handleRegister)
	mux.HandleFunc("/api/auth/login", h.handleLogin)
	mux.HandleFunc("/api/auth/me", h.handleMe)
	mux.HandleFunc("/api/auth/me/preferences", h.handlePreferences)
	mux.HandleFunc("/api/auth/password", h.handleChangePassword)
	mux.HandleFunc("/api/auth/logout", h.handleLogout)
}

func (h *AuthHandler) handleRegister(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req usecase.RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	resp, err := h.registerUseCase.Execute(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *AuthHandler) handleLogin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req usecase.LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	resp, err := h.loginUseCase.Execute(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusUnauthorized)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *AuthHandler) handleChangePassword(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPut {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	userIDStr, ok := middleware.GetUserID(r.Context())
	if !ok {
		http.Error(w, "Authorization required", http.StatusUnauthorized)
		return
	}

	userID, err := uuid.Parse(userIDStr)
	if err != nil {
		http.Error(w, "Invalid user ID", http.StatusUnauthorized)
		return
	}

	var body struct {
		CurrentPassword string `json:"current_password"`
		NewPassword     string `json:"new_password"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	err = h.changePasswordUseCase.Execute(r.Context(), usecase.ChangePasswordRequest{
		UserID:          userID,
		CurrentPassword: body.CurrentPassword,
		NewPassword:     body.NewPassword,
	})
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"message": "password changed successfully"})
}

func (h *AuthHandler) handleMe(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		http.Error(w, "Authorization header required", http.StatusUnauthorized)
		return
	}

	token := strings.TrimPrefix(authHeader, "Bearer ")
	if token == authHeader {
		http.Error(w, "Invalid authorization format", http.StatusUnauthorized)
		return
	}

	resp, err := h.getMeUseCase.Execute(r.Context(), token)
	if err != nil {
		http.Error(w, err.Error(), http.StatusUnauthorized)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *AuthHandler) handleLogout(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		http.Error(w, "Authorization header required", http.StatusUnauthorized)
		return
	}

	token := strings.TrimPrefix(authHeader, "Bearer ")
	if token == authHeader {
		http.Error(w, "Invalid authorization format", http.StatusUnauthorized)
		return
	}

	if err := h.logoutUseCase.Execute(r.Context(), token); err != nil {
		http.Error(w, "Invalid session", http.StatusUnauthorized)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// handlePreferences — PATCH /api/auth/me/preferences
// body: { "preferred_palette": "navy" }   (любое поле опционально)
func (h *AuthHandler) handlePreferences(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPatch {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	userIDStr, ok := middleware.GetUserID(r.Context())
	if !ok {
		http.Error(w, "Authorization required", http.StatusUnauthorized)
		return
	}

	userID, err := uuid.Parse(userIDStr)
	if err != nil {
		http.Error(w, "Invalid user ID", http.StatusUnauthorized)
		return
	}

	var body struct {
		PreferredPalette *string `json:"preferred_palette"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	user, err := h.updatePreferencesUseCase.Execute(r.Context(), usecase.UpdatePreferencesRequest{
		UserID:           userID,
		PreferredPalette: body.PreferredPalette,
	})
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]any{
		"id":                user.ID,
		"email":             user.Email,
		"role":              user.Role,
		"preferred_palette": user.PreferredPalette,
	})
}
