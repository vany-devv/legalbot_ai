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

const streamContent = ref('')
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
    streamContent.value = ''
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
            case 'citations':
              citations.value = (event.data || []).map((c: any) => ({
                id: c.chunk_id,
                score: c.retrieval_score,
                quote: c.content,
                meta: c.meta || {},
              }))
              break
            case 'delta':
              streamContent.value += event.data
              break
            case 'done':
              break
            case 'error':
              error.value = event.text
              break
          }
        }
      }

      // Try parsing the streamed content as JSON
      result.value = parseAnalysisJson(streamContent.value)
    } catch (e: any) {
      error.value = e?.message || 'Не удалось выполнить анализ'
    } finally {
      analyzing.value = false
    }
  }

  return {
    streamContent: readonly(streamContent),
    thinking: readonly(thinking),
    citations: readonly(citations),
    result: readonly(result),
    analyzing: readonly(analyzing),
    error: readonly(error),
    analyze,
    reset,
  }
}

function parseAnalysisJson(raw: string): AnalyzeResult | null {
  let text = raw.trim()
  // Strip markdown code block
  if (text.startsWith('```')) {
    const firstNewline = text.indexOf('\n')
    if (firstNewline !== -1) text = text.slice(firstNewline + 1)
    if (text.endsWith('```')) text = text.slice(0, -3)
    text = text.trim()
  }

  try {
    return JSON.parse(text) as AnalyzeResult
  } catch {
    // Try to find JSON object in text
    const start = text.indexOf('{')
    const end = text.lastIndexOf('}')
    if (start !== -1 && end > start) {
      try {
        return JSON.parse(text.slice(start, end + 1)) as AnalyzeResult
      } catch { /* fallthrough */ }
    }
  }
  return null
}
