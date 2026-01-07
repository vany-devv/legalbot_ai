<template>
  <section>
    <h2>Ответ</h2>
    <label>Вопрос</label>
    <input v-model="query" placeholder="введите вопрос" />
    <label>Top K</label>
    <input v-model.number="topK" type="number" min="1" max="20" />
    <div style="margin-top:8px;">
      <button @click="doAnswer" :disabled="loading">Ответить</button>
    </div>
    <div v-if="resp" style="margin-top:12px;">
      <pre>{{ resp }}</pre>
    </div>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'

const query = ref('какие базовые обязанности по исполнению обязательств у сторон?')
const topK = ref(5)
const loading = ref(false)
const resp = ref('')

async function doAnswer() {
  try {
    loading.value = true
    const r = await axios.post('/api/answer', { query: query.value, top_k: topK.value })
    resp.value = JSON.stringify(r.data, null, 2)
  } catch (e: any) {
    resp.value = e?.response?.data ? JSON.stringify(e.response.data, null, 2) : String(e)
  } finally {
    loading.value = false
  }
}
</script>


