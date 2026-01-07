package domain

// PaymentProvider определяет интерфейс для платежных провайдеров
type PaymentProvider interface {
	CreatePayment(amount int64, currency string, userID string) (string, error) // возвращает payment_id
	VerifyPayment(paymentID string) (bool, error)
	CancelPayment(paymentID string) error
}

