<template>
  <div class="message" :class="[message.role]">
    <div class="message-avatar">
      <div v-if="message.role === 'user'" class="avatar user-avatar">Вы</div>
      <div v-else class="avatar assistant-avatar">LB</div>
    </div>
    <div class="message-body">
      <div class="message-meta">
        <span class="message-role">{{ message.role === 'user' ? 'Вы' : 'LegalBot' }}</span>
        <span v-if="message.provider" class="message-provider">{{ message.provider }} · {{ message.model }}</span>
      </div>
      <div class="message-content" v-html="formatContent(message.content)" />
      <div v-if="message.citations?.length" class="message-citations">
        <div class="citations-label">Источники ({{ message.citations.length }})</div>
        <div class="citations-grid">
          <CitationCard v-for="c in message.citations" :key="c.id" :citation="c" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChatMessage } from '~/composables/useChat'

defineProps<{ message: ChatMessage }>()

function formatContent(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.message {
  display: flex;
  gap: 12px;
  padding: 20px 0;
}
.message + .message { border-top: 1px solid var(--border-light); }

.message-avatar { flex-shrink: 0; }

.avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
}
.user-avatar {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}
.assistant-avatar {
  background: var(--accent);
  color: #fff;
}

.message-body {
  flex: 1;
  min-width: 0;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.message-role {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.message-provider {
  font-size: 12px;
  color: var(--text-tertiary);
}

.message-content {
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-primary);
  word-break: break-word;
}

.message-citations {
  margin-top: 12px;
}
.citations-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.citations-grid {
  display: grid;
  gap: 6px;
}
</style>
