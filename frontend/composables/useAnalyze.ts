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
const result = ref<AnalyzeResult | null>(null)
const analyzing = ref(false)
const error = ref<string | null>(null)

export function useAnalyze() {
  const config = useRuntimeConfig()
  const api = config.public.apiBase
  const { authHeaders } = useAuth()

  function reset() {
    thinking.value = []
    citations.value = []
    result.value = null
    error.value = null
    analyzing.value = false
  }

  async function analyze(text: string | null, file: File | null, topK = 10) {
    if (analyzing.value) return
    if (!text?.trim() && !file) return

    reset()
    analyzing.value = true

    try {
      const formData = new FormData()
      if (text?.trim()) formData.append('text', text)
      if (file) formData.append('file', file)
      formData.append('top_k', String(topK))

      const response = await fetch(`${api}/analyze/stream`, {
        method: 'POST',
        headers: { ...authHeaders() },
        body: formData,
      })

      if (response.status === 402) {
        useToast().show('Лимит запросов исчерпан. Обновите подписку.', 'error', 6000)
        error.value = 'Лимит запросов исчерпан'
        return
      }
      if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

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
            case 'thinking':
              thinking.value = [...thinking.value, { text: event.text }]
              break
            case 'result':
              result.value = event.data as AnalyzeResult
              break
            case 'citations':
              citations.value = (event.data || []).map((c: any) => ({
                id: c.chunk_id,
                score: c.retrieval_score,
                quote: c.content,
                meta: c.meta || {},
              }))
              break
            case 'error':
              error.value = event.text
              break
          }
        }
      }
    } catch (e: any) {
      error.value = e?.message || 'Не удалось выполнить анализ'
    } finally {
      analyzing.value = false
      useBilling().refresh()
    }
  }

  return {
    thinking: readonly(thinking),
    citations: readonly(citations),
    result: readonly(result),
    analyzing: readonly(analyzing),
    error: readonly(error),
    analyze,
    reset,
  }
}

