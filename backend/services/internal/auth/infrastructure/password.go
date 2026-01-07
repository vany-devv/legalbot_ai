package infrastructure

import (
	"golang.org/x/crypto/bcrypt"
	"legalbot/services/internal/auth/domain"
)

type BcryptPasswordHasher struct{}

func NewBcryptPasswordHasher() domain.PasswordHasher {
	return &BcryptPasswordHasher{}
}

func (h *BcryptPasswordHasher) Hash(password string) (string, error) {
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", err
	}
	return string(hash), nil
}

func (h *BcryptPasswordHasher) Compare(hashed, password string) error {
	return bcrypt.CompareHashAndPassword([]byte(hashed), []byte(password))
}

