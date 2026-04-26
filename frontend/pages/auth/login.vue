<template>
  <div class="relative flex items-center justify-center min-h-screen bg-canvas px-6">

    <!-- Back arrow -->
    <NuxtLink
      to="/"
      class="absolute top-5 left-5 flex items-center justify-center w-11 h-11 rounded-xl text-ink-faint hover:text-ink hover:bg-dimmed transition-colors"
      title="На главную"
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="19" y1="12" x2="5" y2="12"/>
        <polyline points="12 19 5 12 12 5"/>
      </svg>
    </NuxtLink>

    <div class="w-full max-w-[420px] flex flex-col gap-7">

      <!-- Brand -->
      <div class="text-center">
        <div class="inline-flex items-center justify-center mb-5">
          <img src="/favicon.svg" width="80" height="80" alt="LegalBot" class="rounded-2xl" />
        </div>
        <h1 class="text-2xl font-bold text-ink">Вход в LegalBot</h1>
        <p class="text-base text-ink-muted mt-1.5">Введите данные для входа в аккаунт</p>
      </div>

      <!-- Form -->
      <form class="flex flex-col gap-4" @submit.prevent="handleLogin">
        <div class="flex flex-col gap-2">
          <label for="email" class="text-sm font-medium text-ink-muted">Email</label>
          <input
            id="email" v-model="email" type="email" placeholder="you@example.com"
            required autocomplete="email"
            class="auth-input"
          />
        </div>
        <div class="flex flex-col gap-2">
          <label for="password" class="text-sm font-medium text-ink-muted">Пароль</label>
          <div class="relative">
            <input
              id="password" v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
              required autocomplete="current-password"
              class="auth-input pr-10"
            />
            <button
              type="button"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-ink-faint hover:text-ink transition-colors cursor-pointer"
              :title="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
              @click="showPassword = !showPassword"
            >
              <!-- Eye open -->
              <svg v-if="showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <!-- Eye off -->
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="flex items-center justify-between">
          <p v-if="error" class="text-sm text-danger">{{ error }}</p>
          <button
            type="button"
            class="text-sm text-ink-muted hover:text-brand transition-colors cursor-pointer ml-auto"
            @click="onForgotPassword"
          >
            Забыли пароль?
          </button>
        </div>
        <button
          type="submit"
          class="w-full py-3 rounded-lg bg-brand text-white text-sm font-semibold hover:bg-brand-lit transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed mt-1"
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
const { show: showToast } = useToast()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const showPassword = ref(false)

function onForgotPassword() {
  showToast('Для восстановления пароля обратитесь к администратору', 'info')
}

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
  padding: 10px 14px;
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
