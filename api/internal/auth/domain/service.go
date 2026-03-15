package domain

// PasswordHasher определяет интерфейс для хэширования паролей
type PasswordHasher interface {
	Hash(password string) (string, error)
	Compare(hashed, password string) error
}

// TokenGenerator определяет интерфейс для генерации токенов
type TokenGenerator interface {
	Generate(userID string) (string, error)
	Validate(token string) (string, error) // возвращает userID
}

