type Theme = 'dark' | 'light'

const theme = ref<Theme>('dark')

export function useTheme() {
  function init() {
    if (import.meta.server) return
    const saved = localStorage.getItem('lb-theme') as Theme | null
    theme.value = saved === 'light' ? 'light' : 'dark'
    apply()
  }

  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem('lb-theme', theme.value)
    apply()
  }

  function apply() {
    if (import.meta.server) return
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  return { theme: readonly(theme), toggle, init }
}
