<template>
  <div class="chat-page">
    <div class="chat-messages" ref="messagesRef">
      <div v-if="!messages.length" class="chat-welcome">
        <div class="welcome-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
        </div>
        <h1 class="welcome-title">LegalBot AI</h1>
        <p class="welcome-subtitle">Юридический ассистент с поддержкой RAG</p>
        <div class="welcome-hints">
          <button class="hint-btn" @click="sendHint('Какие основные права работника по ТК РФ?')">
            Права работника по ТК РФ
          </button>
          <button class="hint-btn" @click="sendHint('Объясни порядок расторжения договора по ГК РФ')">
            Расторжение договора по ГК
          </button>
          <button class="hint-btn" @click="sendHint('Какие обязательства должны исполняться надлежащим образом?')">
            Надлежащее исполнение обязательств
          </button>
        </div>
      </div>

      <div v-else class="messages-list">
        <ChatMessage v-for="msg in messages" :key="msg.id" :message="msg" />
        <div v-if="sending" class="typing-indicator">
          <div class="typing-dot" /><div class="typing-dot" /><div class="typing-dot" />
        </div>
      </div>
    </div>

    <ChatInput />
  </div>
</template>

<script setup lang="ts">
const { messages, sending, send, newChat } = useChat()
const messagesRef = ref<HTMLElement | null>(null)

onMounted(() => newChat())

function sendHint(query: string) {
  send(query)
}

watch(messages, () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}, { deep: true })
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-chat);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
}

/* ─── Welcome ─── */
.chat-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  padding: 40px 20px;
  text-align: center;
}
.welcome-icon { color: var(--accent); opacity: 0.7; }
.welcome-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}
.welcome-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  max-width: 400px;
}
.welcome-hints {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
  max-width: 600px;
}
.hint-btn {
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.hint-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--text-tertiary);
}

/* ─── Messages ─── */
.messages-list {
  max-width: 780px;
  margin: 0 auto;
  padding: 16px 0;
  width: 100%;
}

/* ─── Typing indicator ─── */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 16px 0 16px 44px;
}
.typing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-tertiary);
  animation: typing 1.2s ease-in-out infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.15s; }
.typing-dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}
</style>
