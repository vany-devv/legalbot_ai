<template>
  <aside
    class="flex flex-col h-screen bg-sidebar border-r border-rim flex-shrink-0 overflow-hidden"
    :class="[sidebarOpen ? 'w-[260px]' : 'w-[52px]', sidebarReady ? 'transition-[width] duration-250 ease-in-out' : '']"
  >
    <!-- ─── Header (logo + collapse) ──────────────────────── -->
    <div class="px-2 pt-2 pb-2 flex-shrink-0">
      <div
        class="flex items-center h-9 px-[10px] rounded-lg overflow-hidden transition-colors"
        :class="!sidebarOpen ? 'cursor-pointer text-ink-faint hover:text-ink hover:bg-dimmed' : 'text-ink'"
        :title="!sidebarOpen ? 'Развернуть' : ''"
        @click="!sidebarOpen && toggle()"
      >
        <button
          class="sidebar-label flex-shrink-0 flex items-center justify-center cursor-pointer"
          :class="!sidebarOpen ? 'label-show' : 'label-hide'"
          title="Развернуть"
          @click.stop="toggle"
        >
          <svg width="17" height="17" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="1.5" y="1.5" width="13" height="13" rx="2"/>
            <line x1="10.5" y1="1.5" x2="10.5" y2="14.5"/>
            <line x1="4" y1="5.5" x2="8.5" y2="5.5"/>
            <line x1="4" y1="8" x2="8.5" y2="8"/>
            <line x1="4" y1="10.5" x2="8.5" y2="10.5"/>
          </svg>
        </button>

        <div
          class="sidebar-label flex items-center gap-1.5 flex-1 min-w-0"
          :class="sidebarOpen ? 'label-show' : 'label-hide'"
        >
          <span class="text-[16px] font-semibold text-ink whitespace-nowrap">LegalBot</span>
          <img src="/favicon.svg" width="20" height="20" alt="LegalBot" class="flex-shrink-0 rounded" />
        </div>

        <button
          class="sidebar-label flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-lg text-ink-faint hover:text-ink hover:bg-dimmed transition-colors cursor-pointer"
          :class="sidebarOpen ? 'label-show' : 'label-hide'"
          title="Свернуть"
          @click.stop="toggle"
        >
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="1.5" y="1.5" width="13" height="13" rx="2"/>
            <line x1="5.5" y1="1.5" x2="5.5" y2="14.5"/>
            <line x1="8" y1="5.5" x2="12" y2="5.5"/>
            <line x1="8" y1="8" x2="12" y2="8"/>
            <line x1="8" y1="10.5" x2="12" y2="10.5"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- ─── Tab switcher (Чат / Анализ) ───────────────────── -->
    <div class="px-2 pb-2 flex-shrink-0">
      <!-- Open: flat two-button row, такой же высоты как "Новый <чат|анализ>" -->
      <div v-if="sidebarOpen" class="flex items-center gap-1" role="tablist">
        <button
          class="sidebar-nav-item flex-1 justify-start"
          :class="currentMode === 'chat' ? 'sidebar-nav-active' : ''"
          role="tab"
          :aria-selected="currentMode === 'chat'"
          @click="switchTo('chat')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <span>Чат</span>
        </button>
        <button
          class="sidebar-nav-item flex-1 justify-start"
          :class="currentMode === 'analyze' ? 'sidebar-nav-active' : ''"
          role="tab"
          :aria-selected="currentMode === 'analyze'"
          @click="switchTo('analyze')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span>Анализ</span>
        </button>
      </div>

      <!-- Collapsed: vertical icon-only buttons -->
      <div v-else class="flex flex-col gap-0.5">
        <button
          class="sidebar-nav-item w-full justify-center"
          :class="currentMode === 'chat' ? 'sidebar-nav-active' : ''"
          title="Чат"
          @click="switchTo('chat')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </button>
        <button
          class="sidebar-nav-item w-full justify-center"
          :class="currentMode === 'analyze' ? 'sidebar-nav-active' : ''"
          title="Анализ"
          @click="switchTo('analyze')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- ─── Primary action: Новый <чат|анализ> ────────────── -->
    <div class="px-2 pb-2 flex-shrink-0">
      <button class="sidebar-nav-item w-full" :title="primaryLabel" @click="handleNewItem">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">{{ primaryLabel }}</span>
      </button>
    </div>

    <!-- ─── Contextual list (chat OR analyses) ────────────── -->
    <div
      class="flex-1 overflow-y-auto px-2 py-1 transition-opacity duration-150"
      :class="sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'"
    >
      <!-- Чаты -->
      <template v-if="currentMode === 'chat'">
        <div v-if="!conversations.length" class="sidebar-nav-item cursor-default opacity-60 pointer-events-none">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0 opacity-60">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <span class="sidebar-label text-ink-faint text-xs" :class="sidebarOpen ? 'label-show' : 'label-hide'">Нет диалогов</span>
        </div>
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="relative flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm transition-all duration-150 mb-0.5 overflow-hidden"
          :class="conv.id === currentConversationId
            ? 'bg-brand-dim text-ink'
            : 'text-ink-muted hover:bg-panel hover:text-ink'"
          @click="handleOpenChat(conv.id)"
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
      </template>

      <!-- Анализы -->
      <template v-else>
        <div v-if="!analyses.length" class="sidebar-nav-item cursor-default opacity-60 pointer-events-none">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0 opacity-60">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span class="sidebar-label text-ink-faint text-xs" :class="sidebarOpen ? 'label-show' : 'label-hide'">Нет анализов</span>
        </div>
        <div
          v-for="a in analyses"
          :key="a.id"
          class="group relative flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm transition-all duration-150 mb-0.5 overflow-hidden"
          :class="a.id === currentAnalysisId
            ? 'bg-brand-dim text-ink'
            : 'text-ink-muted hover:bg-panel hover:text-ink'"
          @click="handleOpenAnalysis(a.id)"
        >
          <span
            v-if="a.id === currentAnalysisId"
            class="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-brand rounded-r-full"
          />
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0 opacity-50">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span class="truncate flex-1">{{ a.title }}</span>
          <button
            class="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded text-ink-faint hover:text-danger opacity-0 group-hover:opacity-100 transition-opacity"
            title="Удалить"
            @click.stop="confirmDeleteAnalysis(a.id)"
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </template>
    </div>

    <!-- ─── Secondary nav + user ──────────────────────────── -->
    <div class="px-2 pb-3 pt-2 border-t border-rim space-y-0.5 flex-shrink-0">
      <NuxtLink v-if="isAdmin" to="/admin" class="sidebar-nav-item" active-class="sidebar-nav-active">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
        <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">База знаний</span>
      </NuxtLink>

      <NuxtLink to="/settings" class="sidebar-nav-item" active-class="sidebar-nav-active">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">Настройки</span>
      </NuxtLink>

      <NuxtLink to="/subscription" class="sidebar-nav-item" active-class="sidebar-nav-active">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
        <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">Подписка</span>
      </NuxtLink>

      <button class="sidebar-nav-item w-full" :title="theme === 'dark' ? 'Светлая тема' : 'Темная тема'" @click="toggleTheme">
        <svg v-if="theme === 'dark'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
        <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">
          {{ theme === 'dark' ? 'Светлая тема' : 'Темная тема' }}
        </span>
      </button>

      <div class="pt-1 mt-1 border-t border-rim">
        <template v-if="isLoggedIn">
          <div class="sidebar-nav-item cursor-default">
            <div class="w-4 h-4 rounded-full bg-brand-dim border border-brand/20 flex items-center justify-center flex-shrink-0">
              <span class="text-[8px] font-bold text-brand uppercase">{{ user?.email?.[0] }}</span>
            </div>
            <span class="sidebar-label text-xs text-ink-muted truncate flex-1 min-w-0" :class="sidebarOpen ? 'label-show' : 'label-hide'">
              {{ user?.email }}
            </span>
            <button
              class="sidebar-label text-xs text-ink-faint hover:text-danger transition-colors cursor-pointer flex-shrink-0"
              :class="sidebarOpen ? 'label-show' : 'label-hide'"
              @click="logout"
            >
              Выйти
            </button>
          </div>
        </template>
        <NuxtLink v-else to="/auth/login" class="sidebar-nav-item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/>
          </svg>
          <span class="sidebar-label" :class="sidebarOpen ? 'label-show' : 'label-hide'">Войти</span>
        </NuxtLink>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import type { SidebarMode } from '~/composables/useSidebar'

const { conversations, currentConversationId, newChat, loadConversations } = useChat()
const { items: analyses, currentId: currentAnalysisId, loadList: loadAnalyses, remove: removeAnalysis } = useAnalysisHistory()
const { user, isLoggedIn, isAdmin, logout } = useAuth()
const { sidebarOpen, sidebarReady, lastMode, toggle, setLastMode } = useSidebar()
const { reset: resetAnalyze } = useAnalyze()
const { theme, toggle: toggleTheme } = useTheme()
const router = useRouter()
const route = useRoute()

onMounted(async () => {
  await Promise.all([loadConversations(), loadAnalyses()])
})

watch(isLoggedIn, async (next) => {
  if (next) {
    await Promise.all([loadConversations(), loadAnalyses()])
  }
})

// Mode определяется по route. На "вторичных" страницах (settings/subscription/admin)
// показываем последний явно выбранный mode через sticky lastMode из localStorage.
const currentMode = computed<SidebarMode>(() => {
  if (route.path.startsWith('/analyze')) return 'analyze'
  if (route.path.startsWith('/chat')) return 'chat'
  return lastMode.value
})

// Обновляем lastMode только когда юзер реально находится на chat- или analyze-странице.
// На settings/subscription/admin sticky mode остаётся прежним.
watch(currentMode, (m) => {
  const onPrimaryPage = route.path.startsWith('/chat') || route.path.startsWith('/analyze')
  if (onPrimaryPage) setLastMode(m)
}, { immediate: true })

const primaryLabel = computed(() => currentMode.value === 'chat' ? 'Новый чат' : 'Новый анализ')

function switchTo(m: SidebarMode) {
  const target = m === 'chat' ? '/chat' : '/analyze'
  // Если уже точно на корне нужного режима — ничего не делаем.
  // А клик "Чат" находясь на /chat/:id ДОЛЖЕН вернуть на /chat (welcome).
  if (route.path === target) return
  router.push(target)
}

function handleNewItem() {
  if (currentMode.value === 'chat') {
    newChat()
    if (route.path !== '/chat') router.push('/chat')
  } else {
    resetAnalyze()
    if (route.path !== '/analyze') router.push('/analyze')
  }
}

function handleOpenChat(id: string) {
  router.push(`/chat/${id}`)
}

function handleOpenAnalysis(id: string) {
  router.push(`/analyze/${id}`)
}

async function confirmDeleteAnalysis(id: string) {
  if (!confirm('Удалить этот анализ?')) return
  await removeAnalysis(id)
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

.sidebar-section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-tertiary);
  padding: 6px 12px 4px;
}

/* max-width has no transition — layout collapses instantly on hide,
   preventing reflow during the sidebar width animation. */
.sidebar-label {
  white-space: nowrap;
  overflow: hidden;
}
.label-show {
  opacity: 1;
  max-width: 200px;
  transition: opacity 0.18s ease;
}
.label-hide {
  opacity: 0;
  max-width: 0;
  transition: opacity 0.1s ease;
}
</style>
