package analysis

import (
	"database/sql"

	"legalbot/services/internal/analysis/handler"
	"legalbot/services/internal/analysis/repository"
	"legalbot/services/internal/analysis/usecase"
	"legalbot/services/internal/ragclient"
)

type Module struct {
	Handler        *handler.AnalysisHandler
	SaveAnalysisUC *usecase.SaveAnalysisUseCase
}

func Wire(db *sql.DB, ragClient *ragclient.Client) *Module {
	repo := repository.NewPostgresAnalysisRepository(db)

	saveUC := usecase.NewSaveAnalysisUseCase(repo)
	listUC := usecase.NewListAnalysesUseCase(repo)
	getUC := usecase.NewGetAnalysisUseCase(repo)
	deleteUC := usecase.NewDeleteAnalysisUseCase(repo)

	return &Module{
		Handler:        handler.NewAnalysisHandler(listUC, getUC, deleteUC, ragClient),
		SaveAnalysisUC: saveUC,
	}
}
