<template>
  <div class="flex flex-col h-full bg-canvas">
    <div ref="messagesRef" class="flex-1 overflow-y-auto px-4">

      <!-- Welcome screen — лого + категориальные карточки -->
      <div v-if="!messages.length" class="flex flex-col items-center justify-center min-h-full gap-8 py-12">

        <!-- Brand: старый логотип + параграф -->
        <div class="flex flex-col items-center gap-4 text-center">
          <img src="/favicon.svg" width="80" height="80" alt="LegalBot" class="rounded-2xl" />
          <div class="flex flex-col gap-1.5">
            <h1 class="text-3xl font-display font-bold tracking-tight text-ink">LegalBot</h1>
            <p class="text-base text-ink-muted max-w-md">Юридический ассистент по законодательству РФ</p>
          </div>
        </div>

        <!-- Category grid -->
        <div class="w-full max-w-[760px] grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <button
            v-for="cat in categories" :key="cat.title"
            class="cat-card group flex items-start gap-3 p-4 rounded-xl border border-rim bg-panel hover:bg-dimmed hover:border-rim-strong transition-all text-left cursor-pointer"
            @click="send(cat.query)"
          >
            <span
              class="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-lg transition-colors"
              :style="{ background: 'var(--accent-subtle)', color: 'var(--accent)' }"
              v-html="cat.icon"
            ></span>
            <div class="flex flex-col gap-0.5 min-w-0">
              <p class="text-[14px] font-semibold text-ink leading-snug">{{ cat.title }}</p>
              <p class="text-[13px] text-ink-muted leading-snug truncate">{{ cat.subtitle }}</p>
            </div>
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

// Замена «pill chips» на категориальные карточки.
// Иконки — inline SVG с currentColor, чтобы наследовать акцентную палитру.
const categories = [
  {
    title: 'Трудовое право',
    subtitle: 'Права работника, увольнение, отпуска',
    query: 'Какие основные права работника по ТК РФ?',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 7h-4V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/></svg>',
  },
  {
    title: 'Договорное право',
    subtitle: 'Расторжение и исполнение договоров',
    query: 'Объясни порядок расторжения договора по ГК РФ',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/></svg>',
  },
  {
    title: 'Реклама и маркетинг',
    subtitle: 'Проверка на 38-ФЗ «О рекламе»',
    query: 'Какие есть запреты в рекламе по 38-ФЗ?',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/></svg>',
  },
  {
    title: 'Защита прав',
    subtitle: 'Потребители, жилищные, семейные споры',
    query: 'Какие у меня права как у потребителя при возврате товара?',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  },
]

const codexCount = 12
const statuteCount = 8

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

watch(() => messages.value.length, () => scrollIfNeeded(true))
watch(messages, () => scrollIfNeeded(false), { deep: true })
</script>

<style scoped>
.cat-card {
  /* лёгкий «лифт» при ховере */
}
.cat-card:hover {
  transform: translateY(-1px);
}

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
