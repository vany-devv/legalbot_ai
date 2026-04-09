const sidebarOpen = ref(true)
const sidebarReady = ref(false)

// Sync init: set correct state before Vue renders (prevents width flash on load)
if (import.meta.client) {
  const saved = localStorage.getItem('lb-sidebar')
  sidebarOpen.value = saved ? saved !== 'closed' : window.innerWidth >= 768
}

export function useSidebar() {
  function init() {
    if (import.meta.server) return
    const saved = localStorage.getItem('lb-sidebar')
    sidebarOpen.value = saved ? saved !== 'closed' : window.innerWidth >= 768
    // Enable transition only after state is settled (prevents animated jitter on load)
    nextTick(() => { sidebarReady.value = true })
  }

  function toggle() {
    sidebarOpen.value = !sidebarOpen.value
    localStorage.setItem('lb-sidebar', sidebarOpen.value ? 'open' : 'closed')
  }

  return { sidebarOpen: readonly(sidebarOpen), sidebarReady: readonly(sidebarReady), toggle, init }
}
