interface User {
  id: string
  email: string
  role: string
  preferred_palette?: string
}

const authRoutes = ['/auth/login', '/auth/register']
const user = ref<User | null>(null)
const loading = ref(false)
const initialized = ref(false)
let initPromise: Promise<void> | null = null

function normalizeInternalPath(candidate: unknown): string | null {
  if (typeof candidate !== 'string' || !candidate.startsWith('/') || candidate.startsWith('//')) {
    return null
  }
  return candidate
}

function isAuthRoute(path: string): boolean {
  const [pathname] = path.split(/[?#]/, 1)
  return authRoutes.includes(pathname || path)
}

// Cleanup для разработчиков с остатками от старой Bearer-схемы.
function clearLegacyTokenStorage() {
  if (!import.meta.client) return
  try {
    localStorage.removeItem('lb-token')
  } catch {
    /* noop */
  }
  // Старую cookie 'lb-token' (не HttpOnly, ставилась Nuxt'ом) удаляем явно.
  document.cookie = 'lb-token=; Path=/; Max-Age=0; SameSite=Lax'
}

export function useAuth() {
  const config = useRuntimeConfig()
  const api = config.public.apiBase

  function clearAuthState() {
    user.value = null
  }

  async function init() {
    if (import.meta.server) return
    if (initialized.value) return
    if (initPromise) return initPromise

    initPromise = (async () => {
      clearLegacyTokenStorage()
      // Cookie летит автоматически с credentials: 'include'.
      // Если не залогинен — fetchMe вернёт 401, user останется null.
      await fetchMe()
      if (user.value) {
        await useBilling().refresh()
      }
    })().finally(() => {
      initialized.value = true
      initPromise = null
    })

    return initPromise
  }

  async function login(email: string, password: string) {
    loading.value = true
    try {
      // Сервер ставит HttpOnly cookie 'lb-session' через Set-Cookie.
      await $fetch(`${api}/auth/login`, {
        method: 'POST',
        body: { Email: email, Password: password },
        credentials: 'include',
      })
      initialized.value = true
      await fetchMe()
      await useBilling().refresh()

      if (user.value?.preferred_palette) {
        const { set: setPalette } = usePalette()
        await setPalette(user.value.preferred_palette as any, { sync: false })
      }
    } finally {
      loading.value = false
    }
  }

  async function register(email: string, password: string) {
    loading.value = true
    try {
      await $fetch(`${api}/auth/register`, {
        method: 'POST',
        body: { Email: email, Password: password },
      })
      await login(email, password)
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    try {
      const res = await $fetch<{
        ID: string
        Email: string
        Role: string
        PreferredPalette: string
      }>(`${api}/auth/me`, { credentials: 'include' })
      user.value = {
        id: res.ID,
        email: res.Email,
        role: res.Role || 'user',
        preferred_palette: res.PreferredPalette || 'navy',
      }
    } catch (e: any) {
      if (e?.status === 401 || e?.statusCode === 401) {
        // Cookie не валидна / отсутствует — просто чистим state.
        // Редирект делает watcher в app.vue.
        clearAuthState()
      }
    }
  }

  async function logout() {
    try {
      await $fetch(`${api}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      })
    } catch {
      // Cookie уже невалидна — серверу нечего удалять, всё ок.
    }
    // Редирект делает watcher в app.vue (на user → null).
    clearAuthState()
  }

  async function changePassword(currentPassword: string, newPassword: string) {
    await $fetch(`${api}/auth/password`, {
      method: 'PUT',
      body: { current_password: currentPassword, new_password: newPassword },
      credentials: 'include',
    })
    // Сервер инвалидирует все сессии и чистит cookie — разлогиниваемся.
    clearAuthState()
  }

  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function buildLoginRedirect(nextPath?: unknown) {
    const safeNext = normalizeInternalPath(nextPath)
    if (!safeNext || isAuthRoute(safeNext)) return '/auth/login'
    return `/auth/login?next=${encodeURIComponent(safeNext)}`
  }

  function resolvePostAuthRedirect(nextPath?: unknown) {
    const safeNext = normalizeInternalPath(nextPath)
    if (!safeNext || isAuthRoute(safeNext)) return '/'
    return safeNext
  }

  return {
    user: readonly(user),
    loading: readonly(loading),
    initialized: readonly(initialized),
    isLoggedIn,
    isAdmin,
    init,
    login,
    register,
    logout,
    changePassword,
    fetchMe,
    clearAuthState,
    buildLoginRedirect,
    resolvePostAuthRedirect,
  }
}
