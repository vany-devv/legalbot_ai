<template>
  <section>
    <h2>Поиск</h2>
    <label>Запрос</label>
    <input v-model="query" placeholder="введите запрос" />
    <label>Top K</label>
    <input v-model.number="topK" type="number" min="1" max="20" />
    <div style="margin-top:8px;">
      <button @click="doSearch" :disabled="loading">Искать</button>
    </div>
    <div v-if="resp" style="margin-top:12px;">
      <pre>{{ resp }}</pre>
    </div>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'

const query = ref('обязательства должны исполняться надлежащим образом')
const topK = ref(5)
const loading = ref(false)
const resp = ref('')

async function doSearch() {
  try {
    loading.value = true
    const r = await axios.post('/api/search', { query: query.value, top_k: topK.value })
    resp.value = JSON.stringify(r.data, null, 2)
  } catch (e: any) {
    resp.value = e?.response?.data ? JSON.stringify(e.response.data, null, 2) : String(e)
  } finally {
    loading.value = false
  }
}
</script>


