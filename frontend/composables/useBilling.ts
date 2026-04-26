interface BillingInfo {
  plan_slug: string
  plan_name: string
  status: string
  used_requests: number
  limit_requests: number
  expires_at: string | null
}

const billing = ref<BillingInfo | null>(null)
const loading = ref(false)

export function useBilling() {
  const config = useRuntimeConfig()
  const api = config.public.apiBase
  const { authHeaders, isLoggedIn } = useAuth()

  async function refresh() {
    if (!isLoggedIn.value) {
      billing.value = null
      return
    }
    loading.value = true
    try {
      billing.value = await $fetch<BillingInfo>(`${api}/billing/me`, {
        headers: authHeaders(),
      })
    } catch {
      billing.value = null
    } finally {
      loading.value = false
    }
  }

  const remaining = computed(() => {
    if (!billing.value) return 0
    return Math.max(0, billing.value.limit_requests - billing.value.used_requests)
  })

  const usagePercent = computed(() => {
    if (!billing.value || billing.value.limit_requests === 0) return 0
    return Math.min(100, Math.round((billing.value.used_requests / billing.value.limit_requests) * 100))
  })

  return {
    billing: readonly(billing),
    loading: readonly(loading),
    remaining,
    usagePercent,
    refresh,
  }
}
