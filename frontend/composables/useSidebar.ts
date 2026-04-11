import { ref, readonly, nextTick } from 'vue'

// Sync read before first render — prevents layout shift on load
const sidebarOpen = ref(
  typeof window !== 'undefined'
    ? (localStorage.getItem('lb-sidebar') ?? 'open') !== 'closed'
    : true
)
const sidebarReady = ref(false)

export function useSidebar() {
  function init() {
    if (typeof window === 'undefined') return
    nextTick(() => { sidebarReady.value = true })
  }

  function toggle() {
    sidebarOpen.value = !sidebarOpen.value
    localStorage.setItem('lb-sidebar', sidebarOpen.value ? 'open' : 'closed')
  }

  return { sidebarOpen: readonly(sidebarOpen), sidebarReady: readonly(sidebarReady), toggle, init }
}
