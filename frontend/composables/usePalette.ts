/**
 * usePalette — управление акцентной палитрой (независимо от светлой/тёмной темы).
 *
 * Hierarchy:
 *  1. localStorage 'lb-palette' (мгновенно при загрузке)
 *  2. user.preferred_palette (из /api/auth/me, синхронизируется при логине)
 *  3. default 'navy'
 *
 * При смене палитры:
 *  - применяется к <html data-palette="...">
 *  - сохраняется в localStorage
 *  - если пользователь авторизован — отправляется PATCH /api/auth/me/preferences
 */

export type Palette = 'indigo' | 'navy' | 'bordeaux' | 'emerald' | 'graphite'

export const PALETTES: Array<{ id: Palette; label: string; sublabel: string; preview: string }> = [
  { id: 'indigo',   label: 'Indigo (Refined)', sublabel: 'INDIGO',   preview: '#4F46E5' },
  { id: 'navy',     label: 'Navy (Classic)',   sublabel: 'NAVY',     preview: '#2A4F82' },
  { id: 'bordeaux', label: 'Bordeaux',         sublabel: 'BORDEAUX', preview: '#7C1D1D' },
  { id: 'emerald',  label: 'Emerald',          sublabel: 'EMERALD',  preview: '#0E7C53' },
  { id: 'graphite', label: 'Graphite Mono',    sublabel: 'GRAPHITE', preview: '#353B50' },
]

const palette = ref<Palette>('navy')

export function usePalette() {
  const config = useRuntimeConfig()
  const api = config.public.apiBase
  const { user, isLoggedIn } = useAuth()

  function init() {
    if (import.meta.server) return
    const saved = localStorage.getItem('lb-palette') as Palette | null
    if (saved && isValidPalette(saved)) {
      palette.value = saved
    } else if (user.value?.preferred_palette && isValidPalette(user.value.preferred_palette as Palette)) {
      palette.value = user.value.preferred_palette as Palette
    }
    apply()
  }

  async function set(next: Palette, { sync = true } = {}) {
    if (!isValidPalette(next)) return
    palette.value = next
    if (import.meta.client) {
      localStorage.setItem('lb-palette', next)
      apply()
    }
    if (sync && isLoggedIn.value) {
      try {
        await $fetch(`${api}/auth/me/preferences`, {
          method: 'PATCH',
          credentials: 'include',
          body: { preferred_palette: next },
        })
      } catch (e) {
        // тихо: палитра уже применена локально
        console.warn('Failed to sync palette to backend:', e)
      }
    }
  }

  function apply() {
    if (import.meta.server) return
    const html = document.documentElement
    html.classList.add('no-transition')
    html.setAttribute('data-palette', palette.value)
    requestAnimationFrame(() => {
      requestAnimationFrame(() => html.classList.remove('no-transition'))
    })
  }

  return {
    palette: readonly(palette),
    palettes: PALETTES,
    init,
    set,
  }
}

function isValidPalette(value: string): value is Palette {
  return ['indigo', 'navy', 'bordeaux', 'emerald', 'graphite'].includes(value)
}
