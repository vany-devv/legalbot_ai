<template>
  <div class="px-4 pb-4 max-w-[780px] mx-auto w-full">
    <div class="input-wrap flex items-center gap-2 px-4 py-2.5 bg-field border border-rim rounded-2xl transition-colors">
      <textarea
        ref="textareaRef"
        v-model="text"
        class="flex-1 bg-transparent text-ink text-[15px] leading-relaxed resize-none outline-none max-h-[200px] placeholder-ink-faint"
        placeholder="Задайте юридический вопрос..."
        rows="1"
        @keydown.enter.exact.prevent="handleSend"
        @input="autoResize"
      />
      <button
        class="flex items-center justify-center w-9 h-9 rounded-xl bg-brand text-white flex-shrink-0 cursor-pointer transition-all hover:bg-brand-lit disabled:opacity-40 disabled:cursor-not-allowed"
        :disabled="!text.trim() || sending"
        @click="handleSend"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
      </button>
    </div>
    <p class="text-center text-[11px] text-ink-faint mt-2">
      LegalBot может допускать ошибки. Проверяйте важную информацию.
    </p>
  </div>
</template>

<script setup lang="ts">
const { send, sending } = useChat()
const text = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function handleSend() {
  if (!text.value.trim() || sending.value) return
  send(text.value.trim())
  text.value = ''
  nextTick(() => autoResize())
}

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 200) + 'px'
}
</script>

<style scoped>
.input-wrap:focus-within { border-color: var(--accent); }
</style>
