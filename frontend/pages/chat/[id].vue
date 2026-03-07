<template>
  <div class="chat-page">
    <div class="chat-messages" ref="messagesRef">
      <div v-if="!messages.length" class="chat-loading">
        <p class="chat-loading-text">Загрузка диалога...</p>
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
const route = useRoute()
const { messages, sending, openConversation } = useChat()
const messagesRef = ref<HTMLElement | null>(null)

onMounted(() => {
  const id = route.params.id as string
  if (id) openConversation(id)
})

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

.chat-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
.chat-loading-text {
  color: var(--text-tertiary);
  font-size: 15px;
}

.messages-list {
  max-width: 780px;
  margin: 0 auto;
  padding: 16px 0;
  width: 100%;
}

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
