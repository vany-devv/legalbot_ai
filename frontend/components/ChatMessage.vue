<template>
  <div class="flex gap-3 py-5 border-b border-rim-faint last:border-b-0">
    <!-- Avatar -->
    <div class="flex-shrink-0">
      <div
        v-if="message.role === 'user'"
        class="w-8 h-8 rounded-full bg-raised flex items-center justify-center text-[11px] font-bold text-ink-muted"
      >
        Вы
      </div>
      <div
        v-else
        class="w-8 h-8 rounded-full bg-brand flex items-center justify-center text-[11px] font-bold text-white"
      >
        LB
      </div>
    </div>

    <!-- Body -->
    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2 mb-2">
        <span class="text-sm font-semibold text-ink">
          {{ message.role === 'user' ? 'Вы' : 'LegalBot' }}
        </span>
        <span v-if="message.provider && !message.isStreaming" class="text-xs text-ink-faint">
          {{ message.provider }} · {{ message.model }}
        </span>
      </div>

      <!-- Thinking block (assistant only) -->
      <ThinkingBlock
        v-if="message.role === 'assistant' && message.thinking?.length"
        :steps="message.thinking"
        :is-streaming="!!message.isStreaming"
        :citations-count="message.citations?.length ?? 0"
      />

      <!-- Content -->
      <div
        v-if="message.content"
        class="prose text-[15px] leading-[1.75] text-ink"
        v-html="formatContent(message.content)"
      />
      <!-- Streaming cursor when no content yet -->
      <span v-else-if="message.isStreaming" class="streaming-cursor" />

      <!-- Streaming cursor at end of content -->
      <span v-if="message.isStreaming && message.content" class="streaming-cursor ml-0.5" />

      <!-- Citations (collapsed by default) -->
      <div v-if="message.citations?.length" class="mt-4">
        <button
          class="flex items-center gap-1.5 text-[11px] font-semibold text-ink-faint uppercase tracking-wider hover:text-ink-muted transition-colors cursor-pointer select-none mb-2"
          @click="citationsOpen = !citationsOpen"
        >
          <svg
            width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
            class="transition-transform duration-150 flex-shrink-0"
            :class="citationsOpen ? 'rotate-0' : '-rotate-90'"
          >
            <polyline points="6 9 12 15 18 9"/>
          </svg>
          Источники ({{ message.citations.length }})
        </button>
        <Transition name="citations-expand">
          <div v-if="citationsOpen" class="grid gap-1.5">
            <CitationCard v-for="c in message.citations" :key="c.id" :citation="c" />
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { marked } from 'marked'
import type { ChatMessage } from '~/composables/useChat'

defineProps<{ message: ChatMessage }>()

const citationsOpen = ref(false)

function formatContent(text: string): string {
  const html = marked.parse(text, { async: false }) as string
  return html.replace(/<table/g, '<div class="table-wrap"><table').replace(/<\/table>/g, '</table></div>')
}
</script>

<style scoped>
.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--accent);
  border-radius: 1px;
  vertical-align: text-bottom;
  animation: blink 0.9s ease-in-out infinite;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.prose { overflow-wrap: break-word; word-break: break-word; min-width: 0; }
.prose :deep(p) { margin-bottom: 0.9em; line-height: 1.75; }
.prose :deep(p:last-child) { margin-bottom: 0; }

.prose :deep(h1) {
  font-size: 18px; font-weight: 700;
  margin: 1.4em 0 0.6em;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 0.3em;
}
.prose :deep(h2) {
  font-size: 16px; font-weight: 700;
  margin: 1.2em 0 0.5em;
  color: var(--text-primary);
}
.prose :deep(h3) {
  font-size: 15px; font-weight: 600;
  margin: 1em 0 0.4em;
  color: var(--text-primary);
}

.prose :deep(ul) { padding-left: 1.4em; margin: 0.5em 0 0.9em; list-style-type: disc; }
.prose :deep(ol) { padding-left: 1.4em; margin: 0.5em 0 0.9em; list-style-type: decimal; }
.prose :deep(li) { margin-bottom: 0.35em; line-height: 1.65; }
.prose :deep(li::marker) { color: var(--accent); }
.prose :deep(li > p) { margin-bottom: 0.3em; }

.prose :deep(strong) { font-weight: 700; color: var(--text-primary); }
.prose :deep(em) { color: var(--text-secondary); font-style: italic; }

.prose :deep(code) {
  background: var(--bg-tertiary); padding: 0.15em 0.4em;
  border-radius: 4px; font-size: 0.875em;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: var(--accent-hover);
}
.prose :deep(pre) {
  background: var(--bg-tertiary); padding: 1em 1.2em;
  border-radius: 8px; overflow-x: auto; margin: 0.8em 0 1em;
  font-size: 0.875em; border: 1px solid var(--border-light);
}
.prose :deep(pre code) { background: none; padding: 0; border-radius: 0; color: var(--text-primary); }

.prose :deep(blockquote) {
  border-left: 3px solid var(--accent); padding: 0.5em 0 0.5em 1em;
  color: var(--text-secondary); margin: 0.8em 0;
  font-style: italic; background: var(--accent-subtle); border-radius: 0 6px 6px 0;
}

.prose :deep(a) { color: var(--accent); text-decoration: underline; text-underline-offset: 2px; }
.prose :deep(a:hover) { color: var(--accent-hover); }
.prose :deep(hr) { border: none; border-top: 1px solid var(--border-light); margin: 1.2em 0; }

.prose :deep(.table-wrap) { overflow-x: auto; margin: 0.8em 0 1em; }
.prose :deep(table) { width: 100%; border-collapse: collapse; font-size: 0.9em; min-width: 400px; }
.prose :deep(th) { text-align: left; padding: 8px 12px; background: var(--bg-tertiary); border: 1px solid var(--border); font-weight: 600; }
.prose :deep(td) { padding: 7px 12px; border: 1px solid var(--border-light); color: var(--text-secondary); }
.prose :deep(tr:hover td) { background: var(--bg-hover); }

.citations-expand-enter-active,
.citations-expand-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.citations-expand-enter-from,
.citations-expand-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
