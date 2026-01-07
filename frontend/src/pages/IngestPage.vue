<template>
  <section>
    <h2>Загрузка документов</h2>
    <p>Формат: массив объектов { id?, text, meta? }.</p>
    <textarea v-model="raw" rows="10" placeholder='[ { "id": "doc-1", "text": "...", "meta": {"act":"..."} } ]'></textarea>
    <div style="margin-top:8px; display:flex; gap:8px;">
      <button @click="loadSample">Заполнить пример</button>
      <button @click="sendIngest" :disabled="loading">Отправить</button>
    </div>
    <div v-if="resp" style="margin-top:12px;">
      <pre>{{ resp }}</pre>
    </div>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'

const raw = ref('')
const loading = ref(false)
const resp = ref('')

function loadSample() {
  raw.value = `[
  {"id":"tc-rf-art-21","text":"Статья 21. Работник имеет право...","meta":{"act":"ТК РФ","article":"21"}},
  {"id":"gk-rf-art-309","text":"Статья 309. Обязательства должны исполняться...","meta":{"act":"ГК РФ","article":"309"}}
]`
}

async function sendIngest() {
  try {
    loading.value = true
    const data = JSON.parse(raw.value)
    const r = await axios.post('/api/ingest', data)
    resp.value = JSON.stringify(r.data, null, 2)
  } catch (e: any) {
    resp.value = e?.response?.data ? JSON.stringify(e.response.data, null, 2) : String(e)
  } finally {
    loading.value = false
  }
}
</script>


