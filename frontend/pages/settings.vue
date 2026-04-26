<template>
  <div class="h-full overflow-y-auto bg-canvas px-6 py-8">
    <div class="max-w-[620px] mx-auto">
      <h1 class="text-2xl font-bold text-ink mb-8">Настройки</h1>

      <!-- Appearance -->
      <section class="mb-8">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-ink-faint pb-2 mb-4 border-b border-rim">
          Внешний вид
        </h2>
        <div class="flex items-center justify-between gap-4 py-3">
          <div>
            <p class="text-[15px] font-medium text-ink">Тема</p>
            <p class="text-sm text-ink-muted">Переключение между темной и светлой темой</p>
          </div>
          <div class="flex border border-rim rounded-lg overflow-hidden">
            <button
              class="flex items-center gap-1.5 px-3.5 py-2 text-sm transition-colors cursor-pointer"
              :class="theme === 'dark' ? 'bg-brand-dim text-brand font-semibold' : 'bg-panel text-ink-muted hover:bg-dimmed'"
              @click="theme !== 'dark' && toggle()"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
              Темная
            </button>
            <button
              class="flex items-center gap-1.5 px-3.5 py-2 text-sm border-l border-rim transition-colors cursor-pointer"
              :class="theme === 'light' ? 'bg-brand-dim text-brand font-semibold' : 'bg-panel text-ink-muted hover:bg-dimmed'"
              @click="theme !== 'light' && toggle()"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
              Светлая
            </button>
          </div>
        </div>
      </section>

      <!-- Subscription -->
      <section v-if="isLoggedIn" class="mb-8">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-ink-faint pb-2 mb-4 border-b border-rim">
          Подписка и лимиты
        </h2>
        <div v-if="billing" class="py-3 flex flex-col gap-3">
          <div class="flex items-center justify-between gap-4">
            <div>
              <p class="text-[15px] font-medium text-ink">Текущий тариф</p>
              <p class="text-sm text-ink-muted">{{ billing.plan_name }}</p>
            </div>
            <NuxtLink
              to="/subscription"
              class="px-4 py-2 rounded-lg border border-rim text-sm text-ink hover:bg-dimmed transition-colors"
            >
              Изменить тариф
            </NuxtLink>
          </div>
          <div class="flex flex-col gap-1.5">
            <div class="flex justify-between text-sm">
              <span class="text-ink-muted">Запросы в месяц</span>
              <span class="text-ink font-medium">
                Осталось: {{ Math.max(0, billing.limit_requests - billing.used_requests) }}/{{ billing.limit_requests }}
              </span>
            </div>
            <div class="h-1.5 bg-rim rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-300"
                :class="usagePercent >= 90 ? 'bg-danger' : usagePercent >= 70 ? 'bg-warning' : 'bg-brand'"
                :style="{ width: usagePercent + '%' }"
              />
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-ink-muted py-3">Загрузка...</p>
      </section>

      <!-- Account -->
      <section class="mb-8">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-ink-faint pb-2 mb-4 border-b border-rim">
          Аккаунт
        </h2>
        <template v-if="isLoggedIn">
          <div class="flex items-center justify-between gap-4 py-3">
            <div>
              <p class="text-[15px] font-medium text-ink">Email</p>
              <p class="text-sm text-ink-muted">{{ user?.email }}</p>
            </div>
          </div>

          <!-- Change password -->
          <div class="py-3">
            <p class="text-[15px] font-medium text-ink mb-3">Смена пароля</p>
            <form class="flex flex-col gap-3 max-w-[360px]" @submit.prevent="handleChangePassword">
              <div class="relative">
                <input
                  v-model="currentPassword"
                  :type="showCurrent ? 'text' : 'password'"
                  placeholder="Текущий пароль"
                  required
                  autocomplete="current-password"
                  class="settings-input pr-10"
                />
                <button type="button" class="eye-btn" @click="showCurrent = !showCurrent">
                  <svg v-if="showCurrent" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
              <div>
                <div class="relative">
                  <input
                    v-model="newPassword"
                    :type="showNew ? 'text' : 'password'"
                    placeholder="Новый пароль"
                    required
                    autocomplete="new-password"
                    class="settings-input pr-10"
                  />
                  <button type="button" class="eye-btn" @click="showNew = !showNew">
                    <svg v-if="showNew" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  </button>
                </div>
                <div v-if="newPassword" class="mt-2 flex items-center gap-2">
                  <div class="flex-1 h-1 rounded-full bg-rim overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-300" :class="strengthBarClass" :style="{ width: strengthPercent + '%' }" />
                  </div>
                  <span class="text-xs whitespace-nowrap" :class="strengthTextClass">{{ strengthLabel }}</span>
                </div>
              </div>
              <div class="relative">
                <input
                  v-model="confirmPassword"
                  :type="showConfirmPw ? 'text' : 'password'"
                  placeholder="Подтвердите новый пароль"
                  required
                  autocomplete="new-password"
                  class="settings-input pr-10"
                />
                <button type="button" class="eye-btn" @click="showConfirmPw = !showConfirmPw">
                  <svg v-if="showConfirmPw" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
              <p v-if="pwError" class="text-sm text-danger">{{ pwError }}</p>
              <p v-if="pwSuccess" class="text-sm text-ok">{{ pwSuccess }}</p>
              <button
                type="submit"
                class="self-start px-4 py-2 rounded-lg bg-brand text-white text-sm font-medium hover:bg-brand-lit transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="pwLoading"
              >
                {{ pwLoading ? 'Сохранение...' : 'Сменить пароль' }}
              </button>
            </form>
          </div>

          <div class="flex items-center justify-between gap-4 py-3">
            <div>
              <p class="text-[15px] font-medium text-ink">Выйти из аккаунта</p>
              <p class="text-sm text-ink-muted">Вы будете перенаправлены на главную страницу</p>
            </div>
            <button
              class="px-4 py-2 rounded-lg border border-danger text-danger text-sm hover:bg-danger/10 transition-colors cursor-pointer"
              @click="handleLogout"
            >
              Выйти
            </button>
          </div>
        </template>
        <template v-else>
          <div class="flex items-center justify-between gap-4 py-3">
            <div>
              <p class="text-[15px] font-medium text-ink">Вы не авторизованы</p>
              <p class="text-sm text-ink-muted">Войдите, чтобы сохранять историю диалогов</p>
            </div>
            <NuxtLink
              to="/auth/login"
              class="px-4 py-2 rounded-lg bg-brand text-white text-sm font-medium hover:bg-brand-lit transition-colors"
            >
              Войти
            </NuxtLink>
          </div>
        </template>
      </section>

      <!-- About -->
      <section>
        <h2 class="text-xs font-semibold uppercase tracking-wider text-ink-faint pb-2 mb-4 border-b border-rim">
          О приложении
        </h2>
        <div class="py-3">
          <p class="text-[15px] font-medium text-ink">LegalBot AI</p>
          <p class="text-sm text-ink-muted">Юридический AI-ассистент для российского рынка. Версия MVP.</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
useHead({ title: 'Настройки' })

const { theme, toggle } = useTheme()
const { user, isLoggedIn, logout, changePassword } = useAuth()
const { billing, usagePercent, refresh: refreshBilling } = useBilling()
const router = useRouter()

onMounted(() => {
  if (isLoggedIn.value) refreshBilling()
})

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showCurrent = ref(false)
const showNew = ref(false)
const showConfirmPw = ref(false)
const pwError = ref('')
const pwSuccess = ref('')
const pwLoading = ref(false)

function getPasswordStrength(pw: string): number {
  if (!pw) return 0
  if (pw.length < 6) return 1
  let score = 0
  if (pw.length >= 8) score++
  if (pw.length >= 10) score++
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++
  if (/\d/.test(pw)) score++
  if (/[^a-zA-Z0-9]/.test(pw)) score++
  if (score <= 1) return 2
  if (score <= 3) return 3
  return 4
}

const strength = computed(() => getPasswordStrength(newPassword.value))
const strengthLabel = computed(() => ['', 'Ненадежный', 'Слабый', 'Средний', 'Надежный'][strength.value])
const strengthBarClass = computed(() => ['', 'bg-danger', 'bg-danger', 'bg-warning', 'bg-ok'][strength.value])
const strengthTextClass = computed(() => ['', 'text-danger', 'text-danger', 'text-warning', 'text-ok'][strength.value])
const strengthPercent = computed(() => [0, 25, 50, 75, 100][strength.value])

async function handleChangePassword() {
  pwError.value = ''
  pwSuccess.value = ''
  if (newPassword.value.length < 6) {
    pwError.value = 'Пароль должен быть не менее 6 символов'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    pwError.value = 'Пароли не совпадают'
    return
  }
  pwLoading.value = true
  try {
    await changePassword(currentPassword.value, newPassword.value)
    pwSuccess.value = 'Пароль успешно изменен'
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (e: any) {
    pwError.value = e?.data || e?.message || 'Ошибка смены пароля'
  } finally {
    pwLoading.value = false
  }
}

function handleLogout() {
  logout()
  router.push('/')
}
</script>

<style scoped>
.settings-input {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
}
.settings-input:focus { border-color: var(--accent); }
.settings-input::placeholder { color: var(--text-tertiary); }
.eye-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: color 0.15s;
}
.eye-btn:hover { color: var(--text-primary); }
</style>
