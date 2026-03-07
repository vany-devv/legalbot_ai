export interface Citation {
  id: string
  score: number
  meta: Record<string, any>
  quote: string
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
      const res = await $fetch<Array<{ id: string; title: string; updated_at: string }>>(`${api}/chat/conversations`, {
        headers,
      })
      conversations.value = (res || []).map(c => ({
        id: c.id,
        title: c.title,
        updatedAt: new Date(c.updated_at),
      }))
    } catch {
      // silently fail
    }
  }

  async function loadMessages(conversationId: string) {
    try {
      const res = await $fetch<{
        ConversationID: string
        Title: string
        Messages: Array<{
          ID: string
          Role: string
          Content: string
          Metadata: Record<string, any>
          Citations: Array<{ ChunkID: string; SourceID: string; Score: number; Quote: string; Meta: Record<string, any> }>
          CreatedAt: string
        }>
      }>(`${api}/chat/conversations/${conversationId}`, {
        headers: authHeaders(),
      })
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
    } catch {
      // silently fail
    }
  }

  async function send(query: string, topK = 8) {
    if (!query.trim() || sending.value) return

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
      createdAt: new Date(),
    }
    messages.value.push(userMsg)
    sending.value = true

    try {
      const body: Record<string, any> = { query, top_k: topK }
      if (currentConversationId.value) {
        body.conversation_id = currentConversationId.value
      }

      const res = await $fetch<{
        answer: string
        citations: Citation[]
        confidence: number
        provider: string
        model: string
        conversation_id: string
        message_id: string
      }>(`${api}/chat/ask`, {
        method: 'POST',
        body,
        headers: authHeaders(),
      })

      if (!currentConversationId.value && res.conversation_id) {
        currentConversationId.value = res.conversation_id
        conversations.value.unshift({
          id: res.conversation_id,
          title: query.slice(0, 80),
          updatedAt: new Date(),
        })
      }

      const assistantMsg: ChatMessage = {
        id: res.message_id || crypto.randomUUID(),
        role: 'assistant',
        content: res.answer,
        citations: res.citations,
        provider: res.provider,
        model: res.model,
        confidence: res.confidence,
        createdAt: new Date(),
      }
      messages.value.push(assistantMsg)
    } catch (e: any) {
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Ошибка: ${e?.data?.error || e?.message || 'не удалось получить ответ'}`,
        createdAt: new Date(),
      }
      messages.value.push(errorMsg)
    } finally {
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
