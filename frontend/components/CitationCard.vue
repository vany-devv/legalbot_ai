<template>
  <div
    class="rounded-lg border border-rim-faint bg-cite overflow-hidden transition-colors"
    :class="expanded ? 'border-rim' : 'hover:border-rim'"
  >
    <!-- Header — always visible -->
    <button
      class="w-full flex items-center gap-2.5 px-3 py-2.5 text-left cursor-pointer group"
      @click="expanded = !expanded"
    >
      <!-- Accent dot -->
      <span class="w-1.5 h-1.5 rounded-full bg-brand opacity-70 flex-shrink-0" />

      <!-- Law name -->
      <span class="flex-1 min-w-0 text-[14px] font-semibold text-ink truncate">
        {{ citation.meta?.law || 'Источник' }}
      </span>

      <!-- Tags -->
      <span v-if="citation.meta?.article" class="flex-shrink-0 text-[11px] text-brand bg-brand-dim px-1.5 py-0.5 rounded font-medium">
        ст. {{ citation.meta.article }}
      </span>
      <span v-if="citation.meta?.chapter" class="flex-shrink-0 text-[11px] text-ink-faint bg-raised px-1.5 py-0.5 rounded hidden sm:inline">
        гл. {{ citation.meta.chapter }}
      </span>

      <!-- Score -->
      <span class="flex-shrink-0 text-[11px] text-ink-faint tabular-nums">
        {{ (citation.score * 100).toFixed(0) }}%
      </span>

      <!-- Expand chevron -->
      <svg
        width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        class="flex-shrink-0 text-ink-faint transition-transform duration-150"
        :class="expanded ? 'rotate-180' : ''"
      >
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>

    <!-- Expanded quote -->
    <Transition name="quote-expand">
      <div v-if="expanded" class="px-3 pb-3 pt-0">
        <div class="border-t border-rim-faint pt-2.5">
          <p class="text-[13px] leading-[1.6] text-ink-muted">{{ citation.quote }}</p>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import type { Citation } from '~/composables/useChat'

defineProps<{ citation: Citation }>()

const expanded = ref(false)
</script>

<style scoped>
.quote-expand-enter-active,
.quote-expand-leave-active {
  transition: opacity 0.15s ease, transform 0.12s ease;
}
.quote-expand-enter-from,
.quote-expand-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
