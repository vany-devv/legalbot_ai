/**
 * useAnalysisHistory — список и доступ к сохранённым проверкам рекламы.
 *
 * REST endpoints (бэк сохраняет анализ автоматически по завершении стрима):
 *   GET    /api/analyses          — список (id, title, created_at)
 *   GET    /api/analyses/:id      — полный объект (ad_text, result, citations)
 *   DELETE /api/analyses/:id
 */

export interface AnalysisListItem {
  id: string
  title: string
  created_at: string
}

export interface AnalysisFull {
  id: string
  title: string
  ad_text: string
  result: any
  citations: any[]
  created_at: string
}

const items = ref<AnalysisListItem[]>([])
const currentId = ref<string | null>(null)
const loading = ref(false)

export function useAnalysisHistory() {
  const config = useRuntimeConfig()
  const api = config.public.apiBase
  const { isLoggedIn } = useAuth()

  async function loadList() {
    if (!isLoggedIn.value) {
      items.value = []
      return
    }
    loading.value = true
    try {
      const res = await $fetch<AnalysisListItem[]>(`${api}/analyses`, {
        credentials: 'include',
      })
      items.value = res || []
    } catch (e: any) {
      // 401 — useAuth уже разлогинит; не показываем тост (это редирект, не баг).
      if (e?.status !== 401 && e?.statusCode !== 401) {
        useToast().show('Не удалось загрузить историю анализов', 'error', 4000)
      }
      items.value = []
    } finally {
      loading.value = false
    }
  }

  async function loadOne(id: string): Promise<AnalysisFull | null> {
    if (!isLoggedIn.value) return null
    try {
      return await $fetch<AnalysisFull>(`${api}/analyses/${id}`, {
        credentials: 'include',
      })
    } catch (e) {
      // Молчаливый null — на странице есть UI-fallback `notFound`.
      console.warn('Failed to load analysis:', e)
      return null
    }
  }

  async function remove(id: string) {
    if (!isLoggedIn.value) return
    try {
      await $fetch(`${api}/analyses/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      })
      items.value = items.value.filter(it => it.id !== id)
      if (currentId.value === id) currentId.value = null
    } catch (e: any) {
      if (e?.status !== 401 && e?.statusCode !== 401) {
        useToast().show('Не удалось удалить анализ', 'error', 4000)
      }
    }
  }

  function reset() {
    items.value = []
    currentId.value = null
    loading.value = false
  }

  const authResetTick = useAuthResetSignal()
  watch(authResetTick, () => reset())

  // Локально добавить новую запись в начало списка (вызывается из useAnalyze
  // при получении SSE-события `saved` — без нового запроса к серверу).
  function prepend(item: AnalysisListItem) {
    items.value = [item, ...items.value.filter(i => i.id !== item.id)]
  }

  return {
    items: readonly(items),
    currentId,
    loading: readonly(loading),
    loadList,
    loadOne,
    remove,
    prepend,
    reset,
  }
}
