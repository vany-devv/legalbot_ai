<template>
  <div
    class="risk-card relative rounded-lg border border-rim bg-panel overflow-hidden"
    :class="{ 'risk-card-clickable': hasFragment }"
    :title="hasFragment ? 'Перейти к фрагменту в тексте' : ''"
    @click="onCardClick"
  >
    <!-- Left color bar -->
    <div
      class="absolute top-2 bottom-2 w-[3px] rounded-full"
      :style="{ background: barColor, left: '6px' }"
    />

    <!-- Header -->
    <div class="flex items-center gap-2.5 px-4 pt-3 pl-[18px]">
      <span
        class="flex-shrink-0 text-[11px] font-bold uppercase px-2 py-0.5 rounded-md tracking-wide"
        :class="badgeClass"
      >
        {{ riskLabel }}
      </span>
      <span class="text-[13px] text-ink-muted flex-1 truncate font-medium">
        {{ risk.law_reference }}
      </span>
      <button
        class="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded text-ink-faint hover:text-ink hover:bg-dimmed transition-colors cursor-pointer"
        title="Действия"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="5" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="19" cy="12" r="1.5"/>
        </svg>
      </button>
    </div>

    <!-- Body -->
    <div class="px-4 pl-[18px] pb-4 pt-2 flex flex-col gap-2.5">
      <!-- Fragment quote -->
      <blockquote
        v-if="hasFragment"
        class="border-l-2 border-rim-strong pl-3 text-[13px] leading-[1.55] text-ink-muted italic"
      >
        &laquo;{{ risk.fragment }}&raquo;
      </blockquote>

      <!-- Description -->
      <p class="text-[13.5px] leading-[1.6] text-ink">{{ risk.description }}</p>

      <!-- Recommendation -->
      <div
        class="rounded-lg px-3 py-2.5 flex gap-2.5 items-start mt-1"
        :style="{ background: 'color-mix(in oklab, var(--accent) 7%, transparent)' }"
      >
        <svg
          width="16" height="16" viewBox="0 0 24 24" fill="currentColor"
          class="flex-shrink-0 mt-[2px]"
          :style="{ color: 'var(--accent)' }"
        >
          <path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z"/>
        </svg>
        <p class="text-[13px] leading-[1.55]">
          <span class="font-semibold mr-1" :style="{ color: 'var(--accent)' }">Рекомендация:</span><span class="text-ink">{{ risk.suggestion }}</span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AdRisk } from '~/composables/useAnalyze'

const props = defineProps<{ risk: AdRisk; idx?: number }>()
const emit = defineEmits<{ 'jump-to-fragment': [idx: number] }>()

function onCardClick(e: MouseEvent) {
  // Игнорим клики по интерактивным элементам внутри карточки (кнопка действий и т.п.).
  const target = e.target as HTMLElement
  if (target.closest('button, a')) return
  if (!hasFragment.value || props.idx === undefined) return
  emit('jump-to-fragment', props.idx)
}

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

const barColor = computed(() => {
  switch (props.risk.risk_level) {
    case 'high':   return 'var(--danger)'
    case 'medium': return 'var(--warning)'
    case 'low':    return '#CA8A04'
    default:       return 'var(--border)'
  }
})

const badgeClass = computed(() => {
  switch (props.risk.risk_level) {
    case 'high':   return 'badge-high'
    case 'medium': return 'badge-medium'
    case 'low':    return 'badge-low'
    default:       return 'bg-raised text-ink-faint'
  }
})
</script>

<style scoped>
.risk-card {
  transition: transform 150ms var(--ease-out, cubic-bezier(0.2, 0.7, 0.2, 1)),
              box-shadow 150ms var(--ease-out, cubic-bezier(0.2, 0.7, 0.2, 1)),
              border-color 150ms ease;
}
.risk-card:hover {
  box-shadow: var(--shadow-sm);
}
.risk-card-clickable {
  cursor: pointer;
}
.risk-card-clickable:hover {
  border-color: color-mix(in oklab, var(--accent) 40%, var(--border));
}

/* ─── Saturated severity badges ─── */
.badge-high {
  background: color-mix(in oklab, var(--danger) 18%, transparent);
  color: var(--danger);
}
.badge-medium {
  background: color-mix(in oklab, var(--warning) 20%, transparent);
  color: var(--warning);
}
.badge-low {
  background: color-mix(in oklab, #CA8A04 22%, transparent);
  color: #CA8A04;
}
</style>
