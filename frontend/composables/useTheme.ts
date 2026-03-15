type Theme = 'dark' | 'light'

const theme = ref<Theme>('dark')

export function useTheme() {
  function init() {
    if (import.meta.server) return
    const saved = localStorage.getItem('lb-theme') as Theme | null
    if (saved === 'light' || saved === 'dark') {
      theme.value = saved
    } else {
      theme.value = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    apply()
  }

  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem('lb-theme', theme.value)
    apply()
  }

  function apply() {
    if (import.meta.server) return
    // Disable all transitions during theme switch to prevent desync flicker
    document.documentElement.classList.add('no-transition')
    document.documentElement.setAttribute('data-theme', theme.value)
    // Re-enable after two frames (ensures paint completes first)
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        document.documentElement.classList.remove('no-transition')
      })
    })
  }

  return { theme: readonly(theme), toggle, init }
}
