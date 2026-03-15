function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2)
}

export interface Citation {
  id: string
  score: number
  meta: Record<string, any>
  quote: string
}

export interface ThinkingStep {
  text: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  provider?: string
  model?: string
  confidence?: number
  createdAt: Date
  isStreaming?: boolean
  thinking?: ThinkingStep[]
}

export interface Conversation {
  id: string
  title: string
  updatedAt: Date
}

const conversations = ref<Conversation[]>([])
const currentConversationId = ref<string | null>(null)
const messages = ref<ChatMessage[]>([])
const sending = ref(false)

export function useChat() {
  const config = useRuntimeConfig()
  const api = config.public.apiBase
  const { authHeaders } = useAuth()

  function newChat() {
    currentConversationId.value = null
    messages.value = []
  }

  function openConversation(id: string) {
    currentConversationId.value = id
    messages.value = []
    loadMessages(id)
  }

  async function loadConversations() {
    try {
      const headers = authHeaders()
      if (!headers.Authorization) return
      const res = await $fetch<Array<{ id: string; title: string; updated_at: string }>>(`${api}/chat/conversations`, { headers })
      conversations.value = (res || []).map(c => ({ id: c.id, title: c.title, updatedAt: new Date(c.updated_at) }))
    } catch { /* silently fail */ }
  }

  async function loadMessages(conversationId: string) {
    try {
      const res = await $fetch<{
        ConversationID: string
        Title: string
        Messages: Array<{
          ID: string; Role: string; Content: string; Metadata: Record<string, any>
          Citations: Array<{ ChunkID: string; SourceID: string; Score: number; Quote: string; Meta: Record<string, any> }>
          CreatedAt: string
        }>
      }>(`${api}/chat/conversations/${conversationId}`, { headers: authHeaders() })
      // Guard against race condition: user may have switched conversations
      if (currentConversationId.value !== conversationId) return
      messages.value = (res.Messages || []).map(m => ({
        id: m.ID,
        role: m.Role as 'user' | 'assistant',
        content: m.Content,
        citations: (m.Citations || []).map(c => ({ id: c.ChunkID, score: c.Score, quote: c.Quote, meta: c.Meta || {} })),
        provider: m.Metadata?.provider,
        model: m.Metadata?.model,
        confidence: m.Metadata?.confidence,
        createdAt: new Date(m.CreatedAt),
      }))
    } catch { /* silently fail */ }
  }

  async function send(query: string, topK = 6) {
    if (!query.trim() || sending.value) return

    messages.value.push({ id: uid(), role: 'user', content: query, createdAt: new Date() })
    sending.value = true

    // Streaming assistant placeholder
    messages.value.push({ id: uid(), role: 'assistant', content: '', isStreaming: true, thinking: [], createdAt: new Date() })
    const msgIndex = messages.value.length - 1

    try {
      const body: Record<string, any> = { query, top_k: topK }
      if (currentConversationId.value) body.conversation_id = currentConversationId.value

      const response = await fetch(`${api}/chat/ask/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(body),
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

          const msg = messages.value[msgIndex]
          if (!msg) continue

          switch (event.type) {
            case 'thinking':
              msg.thinking = [...(msg.thinking || []), { text: event.text }]
              break
            case 'citations':
              msg.citations = (event.data || []).map((c: any) => ({ id: c.id, score: c.score, quote: c.quote, meta: c.meta || {} }))
              break
            case 'delta':
              msg.content += event.data
              break
            case 'done':
              msg.isStreaming = false
              if (!currentConversationId.value && event.conversation_id) {
                currentConversationId.value = event.conversation_id
                conversations.value.unshift({ id: event.conversation_id, title: query.slice(0, 80), updatedAt: new Date() })
              }
              break
            case 'error':
              msg.content = `Ошибка: ${event.text}`
              msg.isStreaming = false
              break
          }
        }
      }
    } catch (e: any) {
      const msg = messages.value[msgIndex]
      if (msg) { msg.content = `Ошибка: ${e?.message || 'не удалось получить ответ'}`; msg.isStreaming = false }
    } finally {
      const msg = messages.value[msgIndex]
      if (msg?.isStreaming) msg.isStreaming = false
      sending.value = false
    }
  }

  return {
    conversations,
    currentConversationId: readonly(currentConversationId),
    messages: readonly(messages),
    sending: readonly(sending),
    newChat,
    openConversation,
    send,
    loadConversations,
  }
}
