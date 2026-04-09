<template>
  <aside
    class="flex flex-col h-screen bg-sidebar border-r border-rim flex-shrink-0 overflow-hidden"
    :class="[sidebarOpen ? 'w-[260px]' : 'w-[52px]', sidebarReady ? 'transition-[width] duration-250 ease-in-out' : '']"
  >

    <!-- ── Header ─────────────────────────────────────── -->
    <div class="px-2 pt-3 pb-2 flex-shrink-0 space-y-1.5">

      <!-- Logo row -->
      <div class="flex items-center h-9 gap-1.5 px-1">

        <!-- Collapsed: sidebar expand icon -->
        <button
          v-if="!sidebarOpen"
          class="w-9 h-9 flex items-center justify-center rounded-lg text-ink-faint hover:text-ink hover:bg-dimmed transition-colors cursor-pointer flex-shrink-0"
          title="Развернуть"
          @click="toggle"
        >
          <svg width="17" height="17" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="1.5" y="1.5" width="13" height="13" rx="2"/>
            <line x1="10.5" y1="1.5" x2="10.5" y2="14.5"/>
            <line x1="4" y1="5.5" x2="8.5" y2="5.5"/>
            <line x1="4" y1="8" x2="8.5" y2="8"/>
            <line x1="4" y1="10.5" x2="8.5" y2="10.5"/>
          </svg>
        </button>

        <!-- Open: logo + app name + collapse button -->
        <template v-else>
          <img src="/favicon.svg" width="22" height="22" alt="LegalBot AI" class="flex-shrink-0 rounded-md" />

          <span class="flex-1 text-sm font-semibold text-ink whitespace-nowrap overflow-hidden">
            LegalBot AI
          </span>

          <button
            class="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-lg text-ink-faint hover:text-ink hover:bg-dimmed transition-colors cursor-pointer"
            title="Свернуть"
            @click="toggle"
          >
            <svg width="17" height="17" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="1.5" y="1.5" width="13" height="13" rx="2"/>
              <line x1="5.5" y1="1.5" x2="5.5" y2="14.5"/>
              <line x1="8" y1="5.5" x2="12" y2="5.5"/>
              <line x1="8" y1="8" x2="12" y2="8"/>
              <line x1="8" y1="10.5" x2="12" y2="10.5"/>
            </svg>
          </button>
        </template>
      </div>

      <!-- New Chat button -->
      <button
        class="relative flex items-center w-full h-9 rounded-lg text-sm font-medium transition-colors duration-[250ms] ease-in-out cursor-pointer overflow-hidden"
        :class="sidebarOpen
          ? 'pl-10 pr-3 border border-rim bg-panel text-ink hover:bg-dimmed'
          : 'border border-transparent text-ink-faint hover:text-ink hover:bg-dimmed'"
        title="Новый чат"
        @click="handleNewChat"
      >
        <!-- Icon absolutely positioned so it never shifts during sidebar animation -->
        <svg
          width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"
          class="absolute left-[14px] top-1/2 -translate-y-1/2"
        >
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">
          Новый чат
        </span>
      </button>
    </div>

    <!-- ── Conversations list (fades via opacity) ───── -->
    <div
      class="flex-1 overflow-y-auto px-2 py-1 transition-opacity duration-150"
      :class="sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'"
    >
      <p v-if="!conversations.length" class="px-3 py-4 text-xs text-ink-faint text-center">
        Нет диалогов
      </p>
      <div
        v-for="conv in conversations"
        :key="conv.id"
        class="relative flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm transition-all duration-150 mb-0.5 overflow-hidden"
        :class="conv.id === currentConversationId
          ? 'bg-brand-dim text-ink'
          : 'text-ink-muted hover:bg-panel hover:text-ink'"
        @click="handleOpen(conv.id)"
      >
        <span
          v-if="conv.id === currentConversationId"
          class="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-brand rounded-r-full"
        />
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0 opacity-50">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="truncate">{{ conv.title }}</span>
      </div>
    </div>

    <!-- ── Bottom nav ──────────────────────────────── -->
    <div class="px-2 pb-3 pt-2 border-t border-rim space-y-0.5 flex-shrink-0">

      <!-- Nav items: icon always, label fades -->
      <NuxtLink to="/admin" class="sidebar-nav-item" active-class="sidebar-nav-active">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
        <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">База знаний</span>
      </NuxtLink>

      <NuxtLink to="/analyze" class="sidebar-nav-item" active-class="sidebar-nav-active">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">Анализ рекламы</span>
      </NuxtLink>

      <NuxtLink to="/settings" class="sidebar-nav-item" active-class="sidebar-nav-active">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">Настройки</span>
      </NuxtLink>

      <NuxtLink to="/subscription" class="sidebar-nav-item" active-class="sidebar-nav-active">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
        <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">Подписка</span>
      </NuxtLink>

      <!-- Theme toggle: inline for label control -->
      <button
        class="sidebar-nav-item w-full"
        :title="theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'"
        @click="toggleTheme"
      >
        <svg v-if="theme === 'dark'" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
        <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
        <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">
          {{ theme === 'dark' ? 'Светлая тема' : 'Тёмная тема' }}
        </span>
      </button>

      <!-- User row -->
      <div class="pt-1 mt-1 border-t border-rim">
        <template v-if="isLoggedIn">
          <div class="flex items-center gap-2 px-2.5 py-2 rounded-lg">
            <div class="w-6 h-6 rounded-full bg-brand-dim border border-brand/20 flex items-center justify-center flex-shrink-0">
              <span class="text-[10px] font-bold text-brand uppercase">{{ user?.email?.[0] }}</span>
            </div>
            <span
              class="text-xs text-ink-muted truncate flex-1 min-w-0 sidebar-label"
              :class="sidebarOpen ? 'label-show' : 'label-hide'"
            >{{ user?.email }}</span>
            <button
              class="text-xs text-ink-faint hover:text-danger transition-[opacity,colors] duration-150 cursor-pointer sidebar-label flex-shrink-0"
              :class="sidebarOpen ? 'label-show' : 'label-hide'"
              @click="logout"
            >
              Выйти
            </button>
          </div>
        </template>
        <NuxtLink v-else to="/auth/login" class="sidebar-nav-item">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/>
          </svg>
          <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">Войти</span>
        </NuxtLink>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
const { conversations, currentConversationId, newChat, loadConversations } = useChat()
const { user, isLoggedIn, logout, init } = useAuth()
const { sidebarOpen, sidebarReady, toggle } = useSidebar()
const { theme, toggle: toggleTheme } = useTheme()
const router = useRouter()

onMounted(async () => {
  init()
  await loadConversations()
})

function handleNewChat() {
  newChat()
  router.push('/')
}

function handleOpen(id: string) {
  router.push(`/chat/${id}`)
}
</script>

<style scoped>
.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  transition: background 0.15s, color 0.15s;
  cursor: pointer;
  overflow: hidden;
}
.sidebar-nav-item:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}
.sidebar-nav-active {
  color: var(--text-primary) !important;
  background: var(--bg-secondary);
}

.sidebar-label {
  white-space: nowrap;
  overflow: hidden;
  transition: opacity 0.18s ease, max-width 0.22s ease;
}
.label-show { opacity: 1; max-width: 180px; }
.label-hide { opacity: 0; max-width: 0; }
</style>
