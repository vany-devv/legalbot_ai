<template>
  <div class="citation-card">
    <div class="citation-header">
      <span class="citation-source">{{ citation.meta?.act || citation.id }}</span>
      <span v-if="citation.meta?.article" class="citation-article">ст. {{ citation.meta.article }}</span>
      <span class="citation-score">{{ (citation.score * 100).toFixed(0) }}%</span>
    </div>
    <p class="citation-quote">{{ citation.quote }}</p>
  </div>
</template>

<script setup lang="ts">
import type { Citation } from '~/composables/useChat'

defineProps<{ citation: Citation }>()
</script>

<style scoped>
.citation-card {
  padding: 10px 12px;
  background: var(--bg-citation);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
}

.citation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
}
.citation-source {
  font-weight: 600;
  color: var(--accent);
}
.citation-article {
  color: var(--text-secondary);
}
.citation-score {
  margin-left: auto;
  color: var(--text-tertiary);
  font-size: 11px;
}

.citation-quote {
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-secondary);
}
</style>
