import { ref, readonly, nextTick } from 'vue'

export type SidebarMode = 'chat' | 'analyze'

// Sync read before first render — prevents layout shift on load
const sidebarOpen = ref(
  typeof window !== 'undefined'
    ? (localStorage.getItem('lb-sidebar') ?? 'open') !== 'closed'
    : true
)
const sidebarReady = ref(false)

// Последний активный режим сайдбара (chat / analyze). Sticky context для
// settings / subscription / admin — чтобы юзер не терял ориентир.
const lastMode = ref<SidebarMode>(
  typeof window !== 'undefined'
    ? ((localStorage.getItem('lb-sidebar-mode') as SidebarMode | null) || 'chat')
    : 'chat'
)

export function useSidebar() {
  function init() {
    if (typeof window === 'undefined') return
    nextTick(() => { sidebarReady.value = true })
  }

  function toggle() {
    sidebarOpen.value = !sidebarOpen.value
    localStorage.setItem('lb-sidebar', sidebarOpen.value ? 'open' : 'closed')
  }

  function setLastMode(m: SidebarMode) {
    if (lastMode.value === m) return
    lastMode.value = m
    localStorage.setItem('lb-sidebar-mode', m)
  }

  return {
    sidebarOpen: readonly(sidebarOpen),
    sidebarReady: readonly(sidebarReady),
    lastMode: readonly(lastMode),
    toggle,
    init,
    setLastMode,
  }
}
