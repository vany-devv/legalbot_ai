import type { Citation, ThinkingStep } from './useChat'

export interface AdRisk {
  fragment: string
  law_reference: string
  risk_level: 'high' | 'medium' | 'low'
  description: string
  suggestion: string
}

export interface AnalyzeResult {
  risks: AdRisk[]
  summary: string
  overall_risk_level: string
}

const thinking = ref<ThinkingStep[]>([])
const citations = ref<Citation[]>([])
// risks/summary/overallRiskLevel — раздельные refs чтобы push на risks работал
// реактивно во время streaming'а (бэк шлёт `risk` события по одному).
const risks = ref<AdRisk[]>([])
const summary = ref<string>('')
const overallRiskLevel = ref<string>('')
const analyzing = ref(false)
const error = ref<string | null>(null)
const materialText = ref<string>('')
const materialTitle = ref<string>('')  // имя файла без расширения, либо title из истории
const savedId = ref<string | null>(null)

// Текущий AbortController стрима — для отмены при unmount / новом запросе / logout.
let currentController: AbortController | null = null

function stripExtension(name: string): string {
  const dot = name.lastIndexOf('.')
  return dot > 0 ? name.slice(0, dot) : name
}

export function useAnalyze() {
  const config = useRuntimeConfig()
  const api = config.public.apiBase
  const { clearAuthState } = useAuth()

  // Computed result — собирает в один объект risks + summary + overall_risk_level
  // чтобы потребители (analyze/index.vue, [id].vue, RiskCard) видели единый объект.
  // При streaming'е каждое push в risks.value автоматически триггерит реактивность.
  const result = computed<AnalyzeResult | null>(() => {
    if (!risks.value.length && !summary.value && !overallRiskLevel.value) return null
    return {
      risks: risks.value,
      summary: summary.value,
      overall_risk_level: overallRiskLevel.value,
    }
  })

  function reset() {
    // Отменяем текущий стрим если он идёт — иначе он продолжит писать в state.
    currentController?.abort()
    currentController = null
    thinking.value = []
    citations.value = []
    risks.value = []
    summary.value = ''
    overallRiskLevel.value = ''
    error.value = null
    analyzing.value = false
    materialText.value = ''
    materialTitle.value = ''
    savedId.value = null
  }

  // На logout / 401 — сбрасываем состояние, чтобы новый юзер не видел чужие данные.
  const authResetTick = useAuthResetSignal()
  watch(authResetTick, () => reset())

  // Подгружаем сохранённый анализ напрямую в состояние (без стрима).
  function loadSaved(payload: {
    id: string
    title?: string
    ad_text: string
    result: any
    citations?: any[]
  }) {
    reset()
    savedId.value = payload.id
    materialText.value = payload.ad_text || ''
    materialTitle.value = payload.title || ''
    const r = (payload.result || {}) as Partial<AnalyzeResult>
    risks.value = r.risks || []
    summary.value = r.summary || ''
    overallRiskLevel.value = r.overall_risk_level || ''
    citations.value = (payload.citations || []).map((c: any) => ({
      id: c.chunk_id ?? c.id,
      score: c.retrieval_score ?? c.score,
      quote: c.content ?? c.quote,
      meta: c.meta || {},
    }))
  }

  async function analyze(text: string | null, file: File | null, topK = 10) {
    if (analyzing.value) return
    if (!text?.trim() && !file) return

    reset()
    analyzing.value = true
    if (file) materialTitle.value = stripExtension(file.name)

    const controller = new AbortController()
    currentController = controller

    try {
      const formData = new FormData()
      if (text?.trim()) formData.append('text', text)
      if (file) formData.append('file', file)
      formData.append('top_k', String(topK))

      const response = await fetch(`${api}/analyze/stream`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
        signal: controller.signal,
      })

      if (response.status === 402) {
        useToast().show('Лимит запросов исчерпан. Обновите подписку.', 'error', 6000)
        error.value = 'Лимит запросов исчерпан'
        return
      }
      if (response.status === 401) {
        clearAuthState()
        return
      }
      if (response.status === 413) {
        error.value = 'Файл слишком большой. Максимум 10 МБ.'
        useToast().show('Файл слишком большой. Максимум 10 МБ.', 'error', 5000)
        return
      }
      if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      // Флаг — пришёл ли хоть один per-risk event. Если да, финальный backward-compat
      // `result` event с агрегатом игнорим (мы уже всё накопили).
      let hasStreamingRisks = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop()!

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const payload = line.slice(6).trim()
          if (payload === '[DONE]') break

          let event: any
          try { event = JSON.parse(payload) } catch { continue }

          switch (event.type) {
            case 'ad_text':
              materialText.value = event.text || ''
              break
            case 'thinking':
              thinking.value = [...thinking.value, { text: event.text }]
              break
            case 'risk':
              if (event.data) {
                risks.value.push(event.data as AdRisk)
                hasStreamingRisks = true
              }
              break
            case 'result_meta':
              summary.value = event.summary || ''
              overallRiskLevel.value = event.overall_risk_level || ''
              break
            case 'result':
              // Backward-compat: финальный агрегат от бэка. Если per-risk уже шли —
              // игнорим (наше состояние уже корректное). Иначе fallback: задаём всё разом.
              if (!hasStreamingRisks && event.data) {
                const data = event.data as AnalyzeResult
                risks.value = data.risks || []
                summary.value = data.summary || ''
                overallRiskLevel.value = data.overall_risk_level || ''
              }
              break
            case 'citations':
              citations.value = (event.data || []).map((c: any) => ({
                id: c.chunk_id,
                score: c.retrieval_score,
                quote: c.content,
                meta: c.meta || {},
              }))
              break
            case 'saved': {
              savedId.value = event.id || null
              // Бэк возвращает финальный title (имя файла без расширения,
              // либо первая фраза текста). Перетираем локальный title.
              if (event.title) materialTitle.value = event.title
              if (event.id) {
                useAnalysisHistory().prepend({
                  id: event.id,
                  title: event.title || 'Без названия',
                  created_at: new Date().toISOString(),
                })
              }
              break
            }
            case 'error':
              error.value = event.text
              break
          }
        }
      }
    } catch (e: any) {
      // Abort — это явная отмена (navigation/logout/новый запрос), не показываем как ошибку.
      if (e?.name !== 'AbortError') {
        error.value = e?.message || 'Не удалось выполнить анализ'
      }
    } finally {
      // Очищаем ссылку только если это всё ещё наш контроллер (могла перебить новая попытка).
      if (currentController === controller) currentController = null
      analyzing.value = false
      useBilling().refresh()
    }
  }

  // Внешний abort — для onBeforeUnmount на странице.
  function abort() {
    currentController?.abort()
  }

  return {
    thinking: readonly(thinking),
    citations: readonly(citations),
    result,  // computed — read-only by nature
    risks: readonly(risks),
    summary: readonly(summary),
    overallRiskLevel: readonly(overallRiskLevel),
    analyzing: readonly(analyzing),
    error: readonly(error),
    materialText: readonly(materialText),
    materialTitle: readonly(materialTitle),
    savedId: readonly(savedId),
    analyze,
    reset,
    abort,
    loadSaved,
  }
}
