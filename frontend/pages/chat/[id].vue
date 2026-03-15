<template>
  <div class="flex flex-col h-full bg-canvas">
    <div ref="messagesRef" class="flex-1 overflow-y-auto px-4">
      <div v-if="!messages.length" class="flex items-center justify-center h-full">
        <p class="text-[15px] text-ink-faint">Загрузка диалога...</p>
      </div>
      <div v-else class="max-w-[780px] mx-auto py-4 w-full">
        <ChatMessage v-for="msg in messages" :key="msg.id" :message="msg" />
        <div v-if="sending" class="flex gap-1 py-4 pl-11">
          <span class="typing-dot" /><span class="typing-dot" /><span class="typing-dot" />
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

function scrollIfNeeded(force = false) {
  nextTick(() => {
    const el = messagesRef.value
    if (!el) return
    const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    if (force || distFromBottom < 120) {
      el.scrollTop = el.scrollHeight
    }
  })
}

watch(() => messages.value.length, () => scrollIfNeeded(true))
watch(messages, () => scrollIfNeeded(false), { deep: true })
</script>

<style scoped>
.typing-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--text-tertiary);
  animation: typing 1.2s ease-in-out infinite;
  display: inline-block;
}
.typing-dot:nth-child(2) { animation-delay: 0.15s; }
.typing-dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}
</style>
