package chat

import (
	"database/sql"

	"legalbot/services/internal/chat/handler"
	"legalbot/services/internal/chat/repository"
	"legalbot/services/internal/chat/usecase"
)

type Module struct {
	Handler            *handler.ChatHandler
	CreateConversation *usecase.CreateConversationUseCase
	SaveMessage        *usecase.SaveMessageUseCase
}

func Wire(db *sql.DB) *Module {
	conversationRepo := repository.NewPostgresConversationRepository(db)
	messageRepo := repository.NewPostgresMessageRepository(db)
	citationRepo := repository.NewPostgresCitationRepository(db)

	createConversationUC := usecase.NewCreateConversationUseCase(conversationRepo)
	saveMessageUC := usecase.NewSaveMessageUseCase(messageRepo, citationRepo)
	getConversationUC := usecase.NewGetConversationUseCase(conversationRepo, messageRepo, citationRepo)
	listConversationsUC := usecase.NewListConversationsUseCase(conversationRepo)

	return &Module{
		Handler:            handler.NewChatHandler(createConversationUC, saveMessageUC, getConversationUC, listConversationsUC),
		CreateConversation: createConversationUC,
		SaveMessage:        saveMessageUC,
	}
}






