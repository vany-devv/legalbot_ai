<template>
  <div class="flex flex-col h-full bg-canvas">
    <div ref="messagesRef" class="flex-1 overflow-y-auto px-4">

      <!-- Welcome screen -->
      <div v-if="!messages.length" class="flex flex-col items-center justify-center h-full gap-5 py-12 text-center">
        <img src="/favicon.svg" width="64" height="64" alt="LegalBot AI" class="rounded-2xl" />
        <div>
          <h1 class="text-2xl font-bold text-ink mb-1.5">LegalBot AI</h1>
          <p class="text-[15px] text-ink-muted max-w-sm">Юридический ассистент</p>
        </div>
        <div class="flex flex-wrap justify-center gap-2 mt-1 max-w-lg">
          <button
            v-for="hint in hints" :key="hint.label"
            class="px-4 py-2 rounded-full border border-rim bg-panel text-ink-muted text-sm hover:bg-dimmed hover:text-ink hover:border-ink-faint transition-all cursor-pointer"
            @click="send(hint.query)"
          >
            {{ hint.label }}
          </button>
        </div>
      </div>

      <!-- Messages -->
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
useHead({ title: 'Чат' })

const { messages, sending, send, newChat } = useChat()
const messagesRef = ref<HTMLElement | null>(null)

const hints = [
  { label: 'Права работника по ТК РФ', query: 'Какие основные права работника по ТК РФ?' },
  { label: 'Расторжение договора по ГК', query: 'Объясни порядок расторжения договора по ГК РФ' },
  { label: 'Исполнение обязательств', query: 'Какие обязательства должны исполняться надлежащим образом?' },
]

onMounted(() => newChat())

// Scroll only when near bottom (prevent jerking during streaming when user scrolled up)
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

// New message added → always scroll
watch(() => messages.value.length, () => scrollIfNeeded(true))

// Content updated (streaming deltas) → only scroll if already near bottom
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
