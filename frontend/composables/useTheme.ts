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

  function set(next: Theme) {
    if (next !== theme.value) {
      theme.value = next
      localStorage.setItem('lb-theme', theme.value)
      apply()
    }
  }

  function toggle() {
    set(theme.value === 'dark' ? 'light' : 'dark')
  }

  function apply() {
    if (import.meta.server) return
    document.documentElement.classList.add('no-transition')
    document.documentElement.setAttribute('data-theme', theme.value)
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        document.documentElement.classList.remove('no-transition')
      })
    })
  }

  return { theme: readonly(theme), toggle, set, init }
}
