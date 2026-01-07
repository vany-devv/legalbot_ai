<template>
  <section class="list">
    <div class="card">
      <h2 style="margin:0 0 8px 0;">Загрузка документов</h2>
      <p class="muted" style="margin:0 0 10px 0;">Формат: массив объектов { id?, text, meta? }.</p>
      <textarea v-model="raw" rows="10" placeholder='[ { "id": "doc-1", "text": "...", "meta": {"act":"..."} } ]'></textarea>
      <div class="spacer"></div>
      <div class="gap">
        <button @click="loadSample">Заполнить пример</button>
        <button @click="sendIngest" :disabled="loading">Отправить</button>
      </div>
    </div>

    <div class="card">
      <h2 style="margin:0 0 8px 0;">Загрузка файла (.doc/.docx, .txt)</h2>
      <p class="muted" style="margin:0 0 10px 0;">
        Поддерживаются только файлы .doc/.docx и .txt (UTF-8 или Windows-1251). Старые .doc рекомендуется сохранить как .docx перед загрузкой.
      </p>
      <input type="file" accept=".doc,.docx,.txt" @change="onFileChange" ref="fileInputEl" />
      <div class="spacer"></div>
      <label>Идентификатор (необязательно)</label>
      <input v-model="fileDocId" placeholder="например, uk-rf-2024" />
      <div class="spacer"></div>
      <button @click="uploadFile" :disabled="fileLoading">Загрузить файл</button>
    </div>

    <div class="card" v-if="result">
      <div class="row">
        <div>Добавлено чанков: <b>{{ result.added_chunks }}</b></div>
        <div class="muted">Всего чанков: {{ result.total_chunks }}</div>
      </div>
    </div>

    <div class="card" v-if="fileResult">
      <div class="row" style="justify-content: space-between;">
        <div>Файл обработан: <b>{{ fileResult.doc_id }}</b></div>
        <div class="muted">Чанков добавлено: {{ fileResult.added_chunks }}</div>
      </div>
      <div class="muted">Всего чанков в стораже: {{ fileResult.total_chunks }}</div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const raw = ref('')
const loading = ref(false)
const result = ref<{added_chunks:number; total_chunks:number} | null>(null)
const file = ref<File | null>(null)
const fileDocId = ref('')
const fileLoading = ref(false)
const fileResult = ref<{added_chunks:number; total_chunks:number; doc_id:string} | null>(null)
const fileInputEl = ref<HTMLInputElement | null>(null)
const config = useRuntimeConfig()

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
    const r = await $fetch<{added_chunks:number; total_chunks:number}>(`${config.public.apiBase}/ingest`, { method: 'POST', body: data })
    result.value = r
  } catch (e: any) {
    result.value = null
    alert(typeof e?.data === 'string' ? e.data : (e?.message || 'Ошибка /ingest'))
  } finally {
    loading.value = false
  }
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const files = target.files
  file.value = files && files.length ? files[0] : null
}

async function uploadFile() {
  if (!file.value) {
    alert('Выберите файл .rtf или .txt')
    return
  }
  try {
    fileLoading.value = true
    const form = new FormData()
    form.append('file', file.value)
    if (fileDocId.value) {
      form.append('doc_id', fileDocId.value.trim())
    }
    const r = await $fetch<{added_chunks:number; total_chunks:number; doc_id:string}>(`${config.public.apiBase}/ingest/upload`, {
      method: 'POST',
      body: form,
    })
    fileResult.value = r
    file.value = null
    fileDocId.value = ''
    if (fileInputEl.value) {
      fileInputEl.value.value = ''
    }
  } catch (e: any) {
    fileResult.value = null
    alert(typeof e?.data === 'string' ? e.data : (e?.message || 'Ошибка загрузки файла'))
  } finally {
    fileLoading.value = false
  }
}
</script>


