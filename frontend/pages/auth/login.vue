<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">LegalBot</div>
      <h1 class="auth-title">Вход в аккаунт</h1>

      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="field">
          <label for="email">Email</label>
          <input id="email" v-model="email" type="email" placeholder="you@example.com" required autocomplete="email" />
        </div>
        <div class="field">
          <label for="password">Пароль</label>
          <input id="password" v-model="password" type="password" placeholder="••••••••" required autocomplete="current-password" />
        </div>
        <div v-if="error" class="auth-error">{{ error }}</div>
        <button type="submit" class="auth-btn" :disabled="loading">
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>

      <p class="auth-footer">
        Нет аккаунта? <NuxtLink to="/auth/register" class="auth-link">Зарегистрироваться</NuxtLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { login, loading } = useAuth()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')

async function handleLogin() {
  error.value = ''
  try {
    await login(email.value, password.value)
    router.push('/')
  } catch (e: any) {
    error.value = e?.data || e?.message || 'Ошибка входа'
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg-primary);
  padding: 24px;
}
.auth-card {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.auth-brand {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent);
  text-align: center;
}
.auth-title {
  font-size: 24px;
  font-weight: 600;
  text-align: center;
  color: var(--text-primary);
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}
.field input {
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 15px;
  outline: none;
  transition: border-color 0.15s;
}
.field input:focus {
  border-color: var(--accent);
}
.auth-error {
  color: var(--danger);
  font-size: 14px;
  text-align: center;
}
.auth-btn {
  padding: 11px 16px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.auth-btn:hover:not(:disabled) { background: var(--accent-hover); }
.auth-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.auth-footer {
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
}
.auth-link {
  color: var(--accent);
  font-weight: 500;
}
.auth-link:hover { text-decoration: underline; }
</style>
