package infrastructure

import (
	"fmt"

	"legalbot/services/internal/billing/domain"
)

// StubPaymentProvider - заглушка для платежного провайдера
// В будущем можно заменить на реальную интеграцию (Stripe, YooKassa и т.д.)
type StubPaymentProvider struct{}

func NewStubPaymentProvider() domain.PaymentProvider {
	return &StubPaymentProvider{}
}

func (p *StubPaymentProvider) CreatePayment(amount int64, currency string, userID string) (string, error) {
	// Заглушка: просто возвращаем ID платежа
	paymentID := fmt.Sprintf("payment_%s_%d", userID, amount)
	return paymentID, nil
}

func (p *StubPaymentProvider) VerifyPayment(paymentID string) (bool, error) {
	// Заглушка: всегда успешно
	return true, nil
}

func (p *StubPaymentProvider) CancelPayment(paymentID string) error {
	// Заглушка: ничего не делаем
	return nil
}






