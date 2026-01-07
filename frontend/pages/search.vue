<template>
  <section class="list">
    <div class="card">
      <h2 style="margin:0 0 8px 0;">Поиск</h2>
      <label>Запрос</label>
      <input v-model="query" placeholder="введите запрос" />
      <div class="spacer"></div>
      <label>Top K</label>
      <input v-model.number="topK" type="number" min="1" max="20" />
      <div class="spacer"></div>
      <button @click="doSearch" :disabled="loading">Искать</button>
    </div>

    <div class="list" v-if="results.length">
      <div class="card" v-for="r in results" :key="r.chunk_id">
        <div class="row" style="justify-content: space-between;">
          <div class="mono">{{ r.chunk_id }}</div>
          <div class="muted">score: {{ r.score.toFixed(3) }}</div>
        </div>
        <div class="muted" style="margin:6px 0;">
          {{ r.meta.act }} {{ r.meta.article ? ('ст. ' + r.meta.article) : '' }}
        </div>
        <div style="white-space: pre-wrap;">{{ r.text }}</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const query = ref('обязательства должны исполняться надлежащим образом')
const topK = ref(5)
const loading = ref(false)
type Item = { doc_id:string; chunk_id:string; score:number; text:string; meta: Record<string, any> }
const results = ref<Item[]>([])

async function doSearch() {
  try {
    loading.value = true
    const r = await $fetch<{query:string; results: Item[]}>(`${config.public.apiBase}/search`, { method: 'POST', body: { query: query.value, top_k: topK.value } })
    results.value = r.results
  } catch (e: any) {
    results.value = []
    alert(typeof e?.data === 'string' ? e.data : (e?.message || 'Ошибка /search'))
  } finally {
    loading.value = false
  }
}
</script>


