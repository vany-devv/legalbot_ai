<template>
  <div class="sub-page">
    <div class="sub-container">
      <h1 class="sub-title">Тарифные планы</h1>
      <p class="sub-subtitle">Выберите подходящий план для вашей работы</p>

      <div class="plans-grid">
        <div class="plan-card">
          <div class="plan-badge">Бесплатно</div>
          <h2 class="plan-name">Базовый</h2>
          <div class="plan-price">
            <span class="price-amount">0 ₽</span>
            <span class="price-period">/ мес</span>
          </div>
          <ul class="plan-features">
            <li>10 запросов в день</li>
            <li>Базовая модель LLM</li>
            <li>Поиск по загруженным документам</li>
          </ul>
          <button class="plan-btn current" disabled>Текущий план</button>
        </div>

        <div class="plan-card featured">
          <div class="plan-badge accent">Популярный</div>
          <h2 class="plan-name">Профессиональный</h2>
          <div class="plan-price">
            <span class="price-amount">1 990 ₽</span>
            <span class="price-period">/ мес</span>
          </div>
          <ul class="plan-features">
            <li>Безлимитные запросы</li>
            <li>Продвинутая модель LLM</li>
            <li>Приоритетная обработка</li>
            <li>История диалогов</li>
            <li>Экспорт ответов</li>
          </ul>
          <button class="plan-btn primary" disabled>Скоро</button>
        </div>

        <div class="plan-card">
          <div class="plan-badge">Для команд</div>
          <h2 class="plan-name">Корпоративный</h2>
          <div class="plan-price">
            <span class="price-amount">Договорная</span>
          </div>
          <ul class="plan-features">
            <li>Всё из «Профессионального»</li>
            <li>Выделенный сервер</li>
            <li>Интеграция с внутренними системами</li>
            <li>SLA и техподдержка</li>
            <li>Обучение на ваших документах</li>
          </ul>
          <button class="plan-btn primary" disabled>Связаться</button>
        </div>
      </div>

      <p class="sub-note">
        Оплата временно недоступна. Функционал подписок находится в разработке.
      </p>
    </div>
  </div>
</template>

<style scoped>
.sub-page {
  height: 100%;
  overflow-y: auto;
  padding: 32px 24px;
  background: var(--bg-chat);
}
.sub-container {
  max-width: 900px;
  margin: 0 auto;
  text-align: center;
}

.sub-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.sub-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 40px;
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.plan-card {
  display: flex;
  flex-direction: column;
  padding: 28px 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  text-align: left;
  transition: border-color 0.2s;
}
.plan-card.featured {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
}

.plan-badge {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}
.plan-badge.accent { color: var(--accent); }

.plan-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.plan-price {
  margin-bottom: 20px;
}
.price-amount {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}
.price-period {
  font-size: 14px;
  color: var(--text-tertiary);
}

.plan-features {
  list-style: none;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 24px;
}
.plan-features li {
  font-size: 14px;
  color: var(--text-secondary);
  padding-left: 20px;
  position: relative;
}
.plan-features li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: var(--success);
  font-weight: 600;
}

.plan-btn {
  width: 100%;
  padding: 10px 16px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.plan-btn.current {
  border: 1px solid var(--border);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: default;
}
.plan-btn.primary {
  border: none;
  background: var(--accent);
  color: #fff;
}
.plan-btn.primary:disabled { opacity: 0.5; cursor: not-allowed; }

.sub-note {
  font-size: 13px;
  color: var(--text-tertiary);
}
</style>
