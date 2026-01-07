package infrastructure

import (
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"legalbot/services/internal/auth/domain"
)

type JWTTokenGenerator struct {
	secret string
}

func NewJWTTokenGenerator(secret string) domain.TokenGenerator {
	return &JWTTokenGenerator{secret: secret}
}

func (g *JWTTokenGenerator) Generate(userID string) (string, error) {
	claims := jwt.MapClaims{
		"user_id": userID,
		"exp":      time.Now().Add(24 * time.Hour).Unix(),
		"iat":      time.Now().Unix(),
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(g.secret))
}

func (g *JWTTokenGenerator) Validate(tokenString string) (string, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(g.secret), nil
	})

	if err != nil {
		return "", err
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		userID, ok := claims["user_id"].(string)
		if !ok {
			return "", fmt.Errorf("invalid token claims")
		}
		return userID, nil
	}

	return "", fmt.Errorf("invalid token")
}

