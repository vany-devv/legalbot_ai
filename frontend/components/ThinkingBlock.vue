<template>
  <div class="thinking-block mb-3">
    <button
      class="flex items-center gap-2 text-sm text-ink-faint hover:text-ink-muted transition-colors cursor-pointer select-none"
      @click="expanded = !expanded"
    >
      <!-- Spinner while streaming, checkmark when done -->
      <span v-if="isStreaming" class="thinking-spinner" />
      <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="text-ok flex-shrink-0">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
      <span>{{ isStreaming ? 'Анализирую...' : label }}</span>
      <svg
        width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
        class="transition-transform duration-150 flex-shrink-0"
        :class="expanded ? 'rotate-180' : ''"
      >
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>

    <Transition name="thinking-expand">
      <div v-if="expanded" class="mt-3 pl-4 border-l-2 border-rim space-y-2.5">
        <div v-for="(step, i) in steps" :key="i" class="flex items-start gap-2.5 text-sm text-ink-faint">
          <span
            v-if="isStreaming && i === steps.length - 1"
            class="thinking-dot flex-shrink-0 mt-1.5"
          />
          <svg v-else width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="text-ok flex-shrink-0 mt-0.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          {{ step.text }}
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import type { ThinkingStep } from '~/composables/useChat'

const props = defineProps<{
  steps: ThinkingStep[]
  isStreaming: boolean
  citationsCount: number
}>()

const expanded = ref(false)

// Auto-open when streaming starts, auto-close when it ends
watch(() => props.isStreaming, (streaming) => {
  expanded.value = streaming
}, { immediate: true })

const label = computed(() => {
  if (props.citationsCount > 0) return `Проанализировано ${props.citationsCount} источников`
  return `Выполнено ${props.steps.length} шага`
})
</script>

<style scoped>
.thinking-spinner {
  width: 13px; height: 13px;
  border: 1.5px solid var(--text-tertiary);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
  flex-shrink: 0;
}
.thinking-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse 1.2s ease-in-out infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pulse { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }

.thinking-expand-enter-active,
.thinking-expand-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.thinking-expand-enter-from,
.thinking-expand-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
