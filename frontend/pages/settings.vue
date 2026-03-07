<template>
  <div class="settings-page">
    <div class="settings-container">
      <h1 class="settings-title">Настройки</h1>

      <section class="settings-section">
        <h2 class="section-heading">Внешний вид</h2>
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-label">Тема</span>
            <span class="setting-desc">Переключение между тёмной и светлой темой</span>
          </div>
          <div class="theme-switcher">
            <button
              class="theme-option"
              :class="{ active: theme === 'dark' }"
              @click="theme !== 'dark' && toggle()"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
              Тёмная
            </button>
            <button
              class="theme-option"
              :class="{ active: theme === 'light' }"
              @click="theme !== 'light' && toggle()"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
              Светлая
            </button>
          </div>
        </div>
      </section>

      <section v-if="isLoggedIn" class="settings-section">
        <h2 class="section-heading">Аккаунт</h2>
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-label">Email</span>
            <span class="setting-desc">{{ user?.email }}</span>
          </div>
        </div>
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-label">Выйти из аккаунта</span>
            <span class="setting-desc">Вы будете перенаправлены на главную страницу</span>
          </div>
          <button class="danger-btn" @click="handleLogout">Выйти</button>
        </div>
      </section>

      <section v-else class="settings-section">
        <h2 class="section-heading">Аккаунт</h2>
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-label">Вы не авторизованы</span>
            <span class="setting-desc">Войдите, чтобы сохранять историю диалогов</span>
          </div>
          <NuxtLink to="/auth/login" class="primary-btn">Войти</NuxtLink>
        </div>
      </section>

      <section class="settings-section">
        <h2 class="section-heading">О приложении</h2>
        <div class="setting-row">
          <div class="setting-info">
            <span class="setting-label">LegalBot AI</span>
            <span class="setting-desc">Юридический AI-ассистент для российского рынка. Версия MVP.</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
const { theme, toggle } = useTheme()
const { user, isLoggedIn, logout } = useAuth()
const router = useRouter()

function handleLogout() {
  logout()
  router.push('/')
}
</script>

<style scoped>
.settings-page {
  height: 100%;
  overflow-y: auto;
  padding: 32px 24px;
  background: var(--bg-chat);
}
.settings-container {
  max-width: 640px;
  margin: 0 auto;
}

.settings-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 32px;
  color: var(--text-primary);
}

.settings-section {
  margin-bottom: 32px;
}

.section-heading {
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.setting-label {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}
.setting-desc {
  font-size: 13px;
  color: var(--text-secondary);
}

.theme-switcher {
  display: flex;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.theme-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.theme-option + .theme-option { border-left: 1px solid var(--border); }
.theme-option.active {
  background: var(--accent-subtle);
  color: var(--accent);
  font-weight: 600;
}
.theme-option:hover:not(.active) { background: var(--bg-hover); }

.danger-btn {
  padding: 8px 16px;
  border: 1px solid var(--danger);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--danger);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.danger-btn:hover { background: rgba(239,68,68,0.1); }

.primary-btn {
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
  text-decoration: none;
}
.primary-btn:hover { background: var(--accent-hover); }
</style>
