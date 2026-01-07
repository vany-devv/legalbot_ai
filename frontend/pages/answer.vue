<template>
  <section class="list">
    <div class="card">
      <h2 style="margin:0 0 8px 0;">Ответ</h2>
      <label>Вопрос</label>
      <input v-model="query" placeholder="введите вопрос" />
      <div class="spacer"></div>
      <label>Top K</label>
      <input v-model.number="topK" type="number" min="1" max="20" />
      <div class="spacer"></div>
      <button @click="doAnswer" :disabled="loading">Ответить</button>
    </div>

    <div class="card" v-if="answer">
      <div class="muted">Провайдер: {{ provider }} · Модель: {{ model }} · Надёжность: {{ confidence.toFixed(2) }}</div>
      <div class="spacer"></div>
      <div style="white-space: pre-wrap;">{{ answer }}</div>
    </div>

    <div class="list" v-if="citations.length">
      <div class="card" v-for="c in citations" :key="c.id">
        <div class="row" style="justify-content: space-between;">
          <div class="mono">{{ c.id }}</div>
          <div class="muted">score: {{ c.score.toFixed(3) }}</div>
        </div>
        <div class="muted" style="margin:6px 0;">
          {{ c.meta?.act }} {{ c.meta?.article ? ('ст. ' + c.meta.article) : '' }}
        </div>
        <div style="white-space: pre-wrap;">{{ c.quote }}</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const query = ref('какие базовые обязанности по исполнению обязательств у сторон?')
const topK = ref(8)
const loading = ref(false)
const answer = ref('')
const provider = ref('')
const model = ref('')
const confidence = ref(0)
type Citation = { id:string; score:number; meta:Record<string, any>; quote:string }
const citations = ref<Citation[]>([])

async function doAnswer() {
  try {
    loading.value = true
    const r = await $fetch<{answer:string; citations:Citation[]; confidence:number; used_chunks:string[]; provider:string; model:string}>(`${config.public.apiBase}/answer`, { method: 'POST', body: { query: query.value, top_k: topK.value } })
    answer.value = r.answer
    provider.value = r.provider
    model.value = r.model
    confidence.value = r.confidence
    citations.value = r.citations
  } catch (e: any) {
    answer.value = ''
    citations.value = []
    alert(typeof e?.data === 'string' ? e.data : (e?.message || 'Ошибка /answer'))
  } finally {
    loading.value = false
  }
}
</script>


