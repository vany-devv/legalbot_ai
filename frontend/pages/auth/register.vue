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
        <h1 class="text-2xl font-bold text-ink">Регистрация</h1>
        <p class="text-base text-ink-muted mt-1.5">Создайте аккаунт для сохранения истории</p>
      </div>

      <!-- Form -->
      <form class="flex flex-col gap-4" @submit.prevent="handleRegister">
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
              placeholder="Минимум 6 символов"
              required autocomplete="new-password"
              class="auth-input pr-10"
            />
            <button
              type="button"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-ink-faint hover:text-ink transition-colors cursor-pointer"
              :title="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
              @click="showPassword = !showPassword"
            >
              <svg v-if="showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label for="confirm" class="text-sm font-medium text-ink-muted">Подтвердите пароль</label>
          <div class="relative">
            <input
              id="confirm" v-model="confirm"
              :type="showConfirm ? 'text' : 'password'"
              placeholder="Повторите пароль"
              required autocomplete="new-password"
              class="auth-input pr-10"
            />
            <button
              type="button"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-ink-faint hover:text-ink transition-colors cursor-pointer"
              :title="showConfirm ? 'Скрыть пароль' : 'Показать пароль'"
              @click="showConfirm = !showConfirm"
            >
              <svg v-if="showConfirm" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
        </div>
        <p v-if="error" class="text-sm text-danger text-center">{{ error }}</p>
        <button
          type="submit"
          class="w-full py-3 rounded-lg bg-brand text-white text-sm font-semibold hover:bg-brand-lit transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed mt-1"
          :disabled="loading"
        >
          {{ loading ? 'Создание...' : 'Создать аккаунт' }}
        </button>
      </form>

      <p class="text-center text-sm text-ink-muted">
        Уже есть аккаунт?
        <NuxtLink to="/auth/login" class="text-brand font-medium hover:underline">Войти</NuxtLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
useHead({ title: 'Регистрация' })

const { register, loading } = useAuth()
const router = useRouter()

const email = ref('')
const password = ref('')
const confirm = ref('')
const error = ref('')
const showPassword = ref(false)
const showConfirm = ref(false)

async function handleRegister() {
  error.value = ''
  if (password.value !== confirm.value) {
    error.value = 'Пароли не совпадают'
    return
  }
  if (password.value.length < 6) {
    error.value = 'Пароль должен быть не менее 6 символов'
    return
  }
  try {
    await register(email.value, password.value)
    router.push('/')
  } catch (e: any) {
    error.value = e?.data || e?.message || 'Ошибка регистрации'
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
