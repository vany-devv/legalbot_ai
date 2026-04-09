<template>
  <div
    class="rounded-lg border overflow-hidden"
    :class="borderClass"
  >
    <!-- Header -->
    <div class="flex items-center gap-2 px-3 py-2.5" :class="headerBgClass">
      <span
        class="flex-shrink-0 text-[11px] font-bold uppercase px-1.5 py-0.5 rounded"
        :class="badgeClass"
      >
        {{ riskLabel }}
      </span>
      <span class="text-[13px] font-medium text-ink truncate">
        {{ risk.law_reference }}
      </span>
    </div>

    <!-- Body -->
    <div class="px-3 py-3 space-y-2.5">
      <!-- Fragment quote -->
      <blockquote v-if="hasFragment" class="border-l-2 pl-3 text-[13px] leading-[1.6] text-ink-muted italic" :class="quoteClass">
        &laquo;{{ risk.fragment }}&raquo;
      </blockquote>

      <!-- Description -->
      <p class="text-[13px] leading-[1.6] text-ink">{{ risk.description }}</p>

      <!-- Suggestion -->
      <div class="flex gap-2 items-start bg-raised rounded px-2.5 py-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="flex-shrink-0 mt-0.5 text-brand">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <span class="text-[12px] leading-[1.5] text-ink-muted">{{ risk.suggestion }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AdRisk } from '~/composables/useAnalyze'

const props = defineProps<{ risk: AdRisk }>()

const hasFragment = computed(() => {
  const f = props.risk.fragment?.trim()
  return f && f !== '[отсутствует в материале]'
})

const riskLabel = computed(() => {
  switch (props.risk.risk_level) {
    case 'high': return 'Высокий'
    case 'medium': return 'Средний'
    case 'low': return 'Низкий'
    default: return props.risk.risk_level
  }
})

const borderClass = computed(() => {
  switch (props.risk.risk_level) {
    case 'high': return 'border-red-500/30'
    case 'medium': return 'border-amber-500/30'
    case 'low': return 'border-yellow-500/30'
    default: return 'border-rim-faint'
  }
})

const headerBgClass = computed(() => {
  switch (props.risk.risk_level) {
    case 'high': return 'bg-red-500/5'
    case 'medium': return 'bg-amber-500/5'
    case 'low': return 'bg-yellow-500/5'
    default: return 'bg-raised'
  }
})

const badgeClass = computed(() => {
  switch (props.risk.risk_level) {
    case 'high': return 'bg-red-500/15 text-red-400'
    case 'medium': return 'bg-amber-500/15 text-amber-400'
    case 'low': return 'bg-yellow-500/15 text-yellow-400'
    default: return 'bg-raised text-ink-faint'
  }
})

const quoteClass = computed(() => {
  switch (props.risk.risk_level) {
    case 'high': return 'border-red-500/40'
    case 'medium': return 'border-amber-500/40'
    case 'low': return 'border-yellow-500/40'
    default: return 'border-rim'
  }
})
</script>
