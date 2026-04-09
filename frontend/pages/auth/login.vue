<template>
  <div class="flex items-center justify-center min-h-screen bg-canvas px-6">
    <div class="w-full max-w-[380px] flex flex-col gap-6">

      <!-- Brand -->
      <div class="text-center">
        <div class="inline-flex items-center justify-center w-11 h-11 rounded-xl mb-4">
          <img src="/favicon.svg" width="44" height="44" alt="LegalBot AI" />
        </div>
        <h1 class="text-xl font-bold text-ink">Вход в LegalBot</h1>
        <p class="text-sm text-ink-muted mt-1">Введите данные для входа в аккаунт</p>
      </div>

      <!-- Form -->
      <form class="flex flex-col gap-4" @submit.prevent="handleLogin">
        <div class="flex flex-col gap-1.5">
          <label for="email" class="text-sm font-medium text-ink-muted">Email</label>
          <input
            id="email" v-model="email" type="email" placeholder="you@example.com"
            required autocomplete="email"
            class="auth-input"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label for="password" class="text-sm font-medium text-ink-muted">Пароль</label>
          <input
            id="password" v-model="password" type="password" placeholder="••••••••"
            required autocomplete="current-password"
            class="auth-input"
          />
        </div>
        <p v-if="error" class="text-sm text-danger text-center">{{ error }}</p>
        <button
          type="submit"
          class="w-full py-2.5 rounded-lg bg-brand text-white text-sm font-semibold hover:bg-brand-lit transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
          :disabled="loading"
        >
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
      </form>

      <p class="text-center text-sm text-ink-muted">
        Нет аккаунта?
        <NuxtLink to="/auth/register" class="text-brand font-medium hover:underline">Зарегистрироваться</NuxtLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
useHead({ title: 'Вход' })

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
.auth-input {
  padding: 9px 13px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 15px;
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
}
.auth-input:focus { border-color: var(--accent); }
.auth-input::placeholder { color: var(--text-tertiary); }
</style>
