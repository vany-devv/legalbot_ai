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
            <p class="text-sm text-ink-muted">Переключение между тёмной и светлой темой</p>
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
              Тёмная
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
const { theme, toggle } = useTheme()
const { user, isLoggedIn, logout } = useAuth()
const router = useRouter()

function handleLogout() {
  logout()
  router.push('/')
}
</script>
