<template>
  <div class="input-bar">
    <div class="input-container">
      <textarea
        ref="textareaRef"
        v-model="text"
        class="input-field"
        placeholder="Задайте юридический вопрос..."
        rows="1"
        @keydown.enter.exact.prevent="handleSend"
        @input="autoResize"
      />
      <button class="send-btn" :disabled="!text.trim() || sending" @click="handleSend">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
    <p class="input-hint">LegalBot может допускать ошибки. Проверяйте важную информацию.</p>
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
.input-bar {
  padding: 0 16px 16px;
  max-width: 780px;
  margin: 0 auto;
  width: 100%;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--bg-input);
  transition: border-color 0.15s;
}
.input-container:focus-within { border-color: var(--accent); }

.input-field {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.5;
  resize: none;
  outline: none;
  max-height: 200px;
}
.input-field::placeholder { color: var(--text-tertiary); }

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s, opacity 0.15s;
}
.send-btn:hover:not(:disabled) { background: var(--accent-hover); }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.input-hint {
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 8px;
}
</style>
