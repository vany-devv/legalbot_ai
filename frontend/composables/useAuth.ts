interface User {
  id: string
  email: string
}

const token = ref<string | null>(null)
const user = ref<User | null>(null)
const loading = ref(false)

export function useAuth() {
  const config = useRuntimeConfig()
  const api = config.public.apiBase

  function init() {
    if (import.meta.server) return
    const saved = localStorage.getItem('lb-token')
    if (saved) {
      token.value = saved
      fetchMe()
    }
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
      token.value = res.Token
      localStorage.setItem('lb-token', res.Token)
      await fetchMe()
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
      const res = await $fetch<{ ID: string; Email: string }>(`${api}/auth/me`, {
        headers: authHeaders(),
      })
      user.value = { id: res.ID, email: res.Email }
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('lb-token')
    if (!import.meta.server) {
      window.location.href = '/'
    }
  }

  const isLoggedIn = computed(() => !!user.value)

  return {
    token: readonly(token),
    user: readonly(user),
    loading: readonly(loading),
    isLoggedIn,
    init,
    login,
    register,
    logout,
    authHeaders,
  }
}
