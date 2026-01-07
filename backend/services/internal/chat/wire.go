package chat

import (
	"database/sql"

	"legalbot/services/internal/chat/handler"
	"legalbot/services/internal/chat/repository"
	"legalbot/services/internal/chat/usecase"
)

// Wire собирает все зависимости домена chat
func Wire(db *sql.DB) *handler.ChatHandler {
	// Repositories
	conversationRepo := repository.NewPostgresConversationRepository(db)
	messageRepo := repository.NewPostgresMessageRepository(db)
	citationRepo := repository.NewPostgresCitationRepository(db)

	// Use cases
	createConversationUC := usecase.NewCreateConversationUseCase(conversationRepo)
	saveMessageUC := usecase.NewSaveMessageUseCase(messageRepo, citationRepo)
	getConversationUC := usecase.NewGetConversationUseCase(conversationRepo, messageRepo, citationRepo)

	// Handler
	return handler.NewChatHandler(createConversationUC, saveMessageUC, getConversationUC)
}






