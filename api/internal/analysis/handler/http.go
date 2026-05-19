package handler

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/google/uuid"
	"legalbot/services/internal/analysis/usecase"
	"legalbot/services/internal/middleware"
	"legalbot/services/internal/ragclient"
)

type AnalysisHandler struct {
	listUC    *usecase.ListAnalysesUseCase
	getUC     *usecase.GetAnalysisUseCase
	deleteUC  *usecase.DeleteAnalysisUseCase
	ragClient *ragclient.Client
}

func NewAnalysisHandler(
	listUC *usecase.ListAnalysesUseCase,
	getUC *usecase.GetAnalysisUseCase,
	deleteUC *usecase.DeleteAnalysisUseCase,
	ragClient *ragclient.Client,
) *AnalysisHandler {
	return &AnalysisHandler{listUC: listUC, getUC: getUC, deleteUC: deleteUC, ragClient: ragClient}
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
	rest := strings.TrimPrefix(r.URL.Path, "/api/analyses/")
	idStr := strings.Split(rest, "/")[0]
	id, err := uuid.Parse(idStr)
	if err != nil {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}

	// GET /api/analyses/:id/report.pdf — премиальный PDF-отчёт.
	if r.Method == http.MethodGet && strings.HasSuffix(r.URL.Path, "/report.pdf") {
		h.handleReport(w, r, id, userID)
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

// handleReport: тянет сохранённый анализ (ownership внутри getUC), форвардит
// в rag /report/pdf, стримит PDF обратно как attachment.
func (h *AnalysisHandler) handleReport(w http.ResponseWriter, r *http.Request, id, userID uuid.UUID) {
	resp, err := h.getUC.Execute(r.Context(), id, userID)
	if err != nil {
		if errors.Is(err, usecase.ErrForbidden) {
			http.Error(w, err.Error(), http.StatusForbidden)
			return
		}
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	payload := struct {
		Title     string          `json:"title"`
		AdText    string          `json:"ad_text"`
		CreatedAt time.Time       `json:"created_at"`
		Result    json.RawMessage `json:"result"`
		Citations json.RawMessage `json:"citations"`
	}{
		Title:     resp.Title,
		AdText:    resp.AdText,
		CreatedAt: resp.CreatedAt,
		Result:    resp.Result,
		Citations: resp.Citations,
	}
	body, err := json.Marshal(payload)
	if err != nil {
		http.Error(w, "failed to build report payload", http.StatusInternalServerError)
		return
	}

	ragResp, err := h.ragClient.GenerateReport(r.Context(), body)
	if err != nil {
		http.Error(w, "failed to generate report", http.StatusBadGateway)
		return
	}
	defer ragResp.Body.Close()

	// Имя файла: ASCII-fallback + RFC 5987 UTF-8 для кириллицы.
	// Чистим символы, недопустимые в имени файла (и многоточие-усечение).
	titleClean := strings.NewReplacer(
		"/", " ", "\\", " ", ":", " ", "*", " ", "?", " ",
		`"`, " ", "<", " ", ">", " ", "|", " ", "…", "",
	).Replace(resp.Title)
	titleClean = strings.Join(strings.Fields(titleClean), " ")
	safe := "LegalBot_report.pdf"
	pretty := "LegalBot_отчёт_" + titleClean + ".pdf"
	w.Header().Set("Content-Type", "application/pdf")
	w.Header().Set("Content-Disposition", fmt.Sprintf(
		`attachment; filename="%s"; filename*=UTF-8''%s`,
		safe, url.PathEscape(pretty),
	))
	w.Header().Set("Cache-Control", "no-store")
	io.Copy(w, ragResp.Body)
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
