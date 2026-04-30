interface User {
  id: string
  email: string
  role: string
  preferred_palette?: string
}

const authRoutes = ['/auth/login', '/auth/register']
const token = ref<string | null>(null)
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

function currentLocationPath(): string {
  if (import.meta.server) return '/'
  return `${window.location.pathname}${window.location.search}${window.location.hash}`
}

export function useAuth() {
  const config = useRuntimeConfig()
  const api = config.public.apiBase
  const router = useRouter()
  const tokenCookie = useCookie<string | null>('lb-token', {
    sameSite: 'lax',
    watch: false,
  })

  function clearAuthState() {
    token.value = null
    user.value = null
    tokenCookie.value = null
    if (import.meta.client) {
      localStorage.removeItem('lb-token')
    }
  }

  function persistToken(nextToken: string) {
    token.value = nextToken
    tokenCookie.value = nextToken
    if (import.meta.client) {
      localStorage.setItem('lb-token', nextToken)
    }
  }

  function readStoredToken() {
    if (token.value) return token.value
    if (import.meta.client) {
      return localStorage.getItem('lb-token') || tokenCookie.value || null
    }
    return tokenCookie.value || null
  }

  function hasStoredToken() {
    return !!readStoredToken()
  }

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

  async function redirectToLogin(nextPath?: string) {
    if (import.meta.server) return
    const target = buildLoginRedirect(nextPath ?? currentLocationPath())
    if (currentLocationPath() === target) return
    await router.replace(target)
  }

  async function handleUnauthorized(nextPath?: string) {
    clearAuthState()
    await redirectToLogin(nextPath)
  }

  async function init() {
    if (import.meta.server) return
    if (initialized.value) return
    if (initPromise) return initPromise

    initPromise = (async () => {
      const saved = readStoredToken()
      if (!saved) {
        clearAuthState()
        return
      }

      persistToken(saved)
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

  function authHeaders(): Record<string, string> {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const res = await $fetch<{ Token: string; UserID: string }>(`${api}/auth/login`, {
        method: 'POST',
        body: { Email: email, Password: password },
      })
      persistToken(res.Token)
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
    if (!token.value) return
    try {
      const res = await $fetch<{
        ID: string
        Email: string
        Role: string
        PreferredPalette: string
      }>(`${api}/auth/me`, {
        headers: authHeaders(),
      })
      user.value = {
        id: res.ID,
        email: res.Email,
        role: res.Role || 'user',
        preferred_palette: res.PreferredPalette || 'navy',
      }
    } catch (e: any) {
      if (e?.status === 401 || e?.statusCode === 401) {
        await handleUnauthorized()
      }
    }
  }

  async function logout() {
    const currentToken = token.value
    try {
      if (currentToken) {
        await $fetch(`${api}/auth/logout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${currentToken}` },
        })
      }
    } catch {
      // Local cleanup still happens if the server session is already gone.
    }
    clearAuthState()
    await router.replace('/auth/login')
  }

  async function changePassword(currentPassword: string, newPassword: string) {
    await $fetch(`${api}/auth/password`, {
      method: 'PUT',
      headers: authHeaders(),
      body: { current_password: currentPassword, new_password: newPassword },
    })
  }

  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  return {
    token: readonly(token),
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
    handleUnauthorized,
    authHeaders,
    buildLoginRedirect,
    resolvePostAuthRedirect,
    hasStoredToken,
  }
}
