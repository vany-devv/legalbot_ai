const sidebarOpen = ref(true)

export function useSidebar() {
  function init() {
    if (import.meta.server) return
    const saved = localStorage.getItem('lb-sidebar')
    if (saved) {
      sidebarOpen.value = saved !== 'closed'
    } else {
      sidebarOpen.value = window.innerWidth >= 768
    }
  }

  function toggle() {
    sidebarOpen.value = !sidebarOpen.value
    localStorage.setItem('lb-sidebar', sidebarOpen.value ? 'open' : 'closed')
  }

  return { sidebarOpen: readonly(sidebarOpen), toggle, init }
}
