<template>
  <div class="h-full overflow-y-auto bg-canvas px-6 py-8">
    <div class="max-w-[840px] mx-auto flex flex-col gap-6">
      <h1 class="text-[22px] font-semibold text-ink">База знаний</h1>

      <!-- Upload card -->
      <div class="bg-panel border border-rim rounded-xl p-6 flex flex-col gap-4">
        <h2 class="text-[15px] font-semibold text-ink">Загрузить документ</h2>

        <!-- Dropzone -->
        <div
          class="dropzone flex flex-col items-center gap-2 py-7 px-6 border-2 border-dashed rounded-lg cursor-pointer transition-all text-sm"
          :class="dragging
            ? 'border-brand bg-brand-dim text-ink-muted'
            : file
              ? 'border-ok bg-ok/5 text-ink'
              : 'border-rim text-ink-faint hover:border-brand hover:bg-brand-dim hover:text-ink-muted'"
          @dragover.prevent="dragging = true"
          @dragleave.prevent="dragging = false"
          @drop.prevent="onDrop"
          @click="fileInput?.click()"
        >
          <input ref="fileInput" type="file" accept=".pdf,.docx,.rtf,.txt" class="hidden" @change="onFileChange" />
          <template v-if="file">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-ok">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
            <span class="font-medium text-[14px]">{{ file.name }}</span>
            <span class="text-xs text-ink-faint">{{ formatSize(file.size) }}</span>
          </template>
          <template v-else>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <span>Выберите или перетащите файл</span>
            <span class="text-xs">PDF, DOCX, RTF</span>
          </template>
        </div>

        <!-- Form fields -->
        <div class="flex gap-3">
          <div class="flex-1 flex flex-col gap-1.5">
            <label class="text-xs font-medium text-ink-muted">Название</label>
            <input v-model="title" type="text" placeholder="Трудовой кодекс РФ" class="admin-input" />
          </div>
          <div class="flex-none w-44 flex flex-col gap-1.5">
            <label class="text-xs font-medium text-ink-muted">Тип документа</label>
            <select v-model="docType" class="admin-input">
              <option value="kodeks">Кодекс</option>
              <option value="fz">Федеральный закон</option>
              <option value="postanovlenie">Постановление</option>
              <option value="other">Другой</option>
            </select>
          </div>
        </div>

        <!-- Alerts -->
        <div v-if="uploadError" class="px-3.5 py-2.5 rounded-lg bg-danger/10 text-danger text-sm">{{ uploadError }}</div>
        <div v-if="uploadSuccess" class="px-3.5 py-2.5 rounded-lg bg-ok/10 text-ok text-sm">{{ uploadSuccess }}</div>

        <!-- Progress -->
        <div v-if="job && (job.status === 'pending' || job.status === 'running')" class="flex flex-col gap-1.5">
          <div class="flex justify-between text-sm text-ink-muted">
            <span>{{ job.status === 'pending' ? 'Ожидание...' : `Обработано ${job.progress} / ${job.total} чанков` }}</span>
            <span>{{ jobProgressPct(job) }}%</span>
          </div>
          <div class="h-1.5 bg-rim rounded-full overflow-hidden">
            <div class="h-full bg-brand rounded-full transition-all duration-400" :style="{ width: jobProgressPct(job) + '%' }" />
          </div>
        </div>

        <button
          class="self-start flex items-center gap-2 px-5 py-2.5 rounded-lg bg-brand text-white text-sm font-medium hover:bg-brand-lit transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!file || !title || uploading"
          @click="upload"
        >
          <span v-if="uploading" class="spinner" />
          {{ uploading ? 'Обработка...' : 'Загрузить' }}
        </button>
      </div>

      <!-- Documents table -->
      <div class="bg-panel border border-rim rounded-xl p-6 flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <h2 class="text-[15px] font-semibold text-ink">Документы</h2>
          <button
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rim text-ink-muted text-xs hover:bg-dimmed hover:text-ink transition-colors cursor-pointer"
            @click="loadDocuments"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Обновить
          </button>
        </div>

        <p v-if="loading" class="text-center py-8 text-sm text-ink-faint">Загрузка...</p>
        <p v-else-if="!documents.length" class="text-center py-8 text-sm text-ink-faint">Документов пока нет</p>
        <table v-else class="w-full text-sm border-collapse">
          <thead>
            <tr>
              <th class="text-left px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-ink-faint border-b border-rim">Название</th>
              <th class="text-left px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-ink-faint border-b border-rim">Тип</th>
              <th class="text-left px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-ink-faint border-b border-rim">Чанков</th>
              <th class="text-left px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-ink-faint border-b border-rim">Обновлен</th>
              <th class="border-b border-rim" />
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in documents" :key="doc.source_id" class="hover:bg-raised transition-colors">
              <td class="px-3 py-2.5 text-ink border-b border-rim-faint max-w-[280px] truncate">{{ doc.title }}</td>
              <td class="px-3 py-2.5 border-b border-rim-faint">
                <span class="px-2 py-0.5 rounded-full bg-brand-dim text-brand text-xs font-medium">
                  {{ docTypeLabel(doc.doc_type) }}
                </span>
              </td>
              <td class="px-3 py-2.5 text-ink-muted border-b border-rim-faint">{{ doc.chunk_count }}</td>
              <td class="px-3 py-2.5 text-ink-muted border-b border-rim-faint">{{ formatDate(doc.updated_at) }}</td>
              <td class="px-3 py-2.5 border-b border-rim-faint">
                <button
                  class="p-1.5 rounded text-ink-faint hover:text-danger hover:bg-danger/8 transition-colors cursor-pointer"
                  @click="deleteDoc(doc.source_id)"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                    <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'admin' })
useHead({ title: 'Администрирование' })

const config = useRuntimeConfig()
const api = config.public.apiBase
const { authHeaders } = useAuth()

const fileInput = ref<HTMLInputElement | null>(null)
const file = ref<File | null>(null)
const title = ref('')
const docType = ref('kodeks')
const dragging = ref(false)
const uploading = ref(false)
const uploadError = ref<string | null>(null)
const uploadSuccess = ref<string | null>(null)

interface IngestJob {
  job_id: string; source_id: string
  status: 'pending' | 'running' | 'done' | 'failed'
  progress: number; total: number; chunks_added: number; error: string | null
}
const job = ref<IngestJob | null>(null)
let pollTimer: ReturnType<typeof setTimeout> | null = null

function jobProgressPct(j: IngestJob) {
  return j.total ? Math.round((j.progress / j.total) * 100) : 0
}
function stopPolling() {
  if (pollTimer) { clearTimeout(pollTimer); pollTimer = null }
  localStorage.removeItem('lb-active-job')
}
async function pollJob(jobId: string) {
  try {
    const j = await $fetch<IngestJob>(`${api}/rag/ingest/jobs/${jobId}`, { headers: authHeaders() })
    job.value = j
    if (j.status === 'done') {
      uploadSuccess.value = `Готово — добавлено ${j.chunks_added} чанков`
      uploading.value = false; stopPolling(); await loadDocuments()
    } else if (j.status === 'failed') {
      uploadError.value = j.error || 'Ошибка обработки'
      uploading.value = false; stopPolling()
    } else {
      pollTimer = setTimeout(() => pollJob(jobId), 2000)
    }
  } catch { pollTimer = setTimeout(() => pollJob(jobId), 3000) }
}

onUnmounted(() => stopPolling())

interface DocInfo {
  id: string; source_id: string; title: string; doc_type: string
  year: number | null; updated_at: string; chunk_count: number
}
const documents = ref<DocInfo[]>([])
const loading = ref(false)

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) setFile(input.files[0])
}
function onDrop(e: DragEvent) {
  dragging.value = false
  if (e.dataTransfer?.files?.[0]) setFile(e.dataTransfer.files[0])
}
function setFile(f: File) {
  file.value = f
  if (!title.value) title.value = f.name.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' ')
}
function formatSize(bytes: number) {
  return bytes > 1_000_000 ? `${(bytes / 1_000_000).toFixed(1)} MB` : `${(bytes / 1_000).toFixed(0)} KB`
}
function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
function docTypeLabel(type: string) {
  return ({ kodeks: 'Кодекс', fz: 'ФЗ', postanovlenie: 'Постановление', other: 'Другой' } as Record<string, string>)[type] ?? type
}

async function upload() {
  if (!file.value || !title.value) return
  uploading.value = true; uploadError.value = null; uploadSuccess.value = null
  job.value = null; stopPolling()
  const form = new FormData()
  form.append('file', file.value)
  form.append('source_id', `${docType.value}-${Date.now()}`)
  form.append('title', title.value)
  form.append('doc_type', docType.value)
  try {
    const res = await $fetch<IngestJob>(`${api}/rag/ingest/upload`, { method: 'POST', body: form, headers: authHeaders() })
    job.value = res; file.value = null; title.value = ''
    if (fileInput.value) fileInput.value.value = ''
    localStorage.setItem('lb-active-job', res.job_id)
    pollTimer = setTimeout(() => pollJob(res.job_id), 1500)
  } catch (e: any) {
    uploadError.value = e?.data?.detail || e?.message || 'Ошибка загрузки'
    uploading.value = false
  }
}

async function loadDocuments() {
  loading.value = true
  try {
    documents.value = await $fetch<DocInfo[]>(`${api}/rag/documents`, { headers: authHeaders() })
  } catch (e: any) {
    uploadError.value = e?.data?.detail || e?.message || 'Не удалось загрузить список документов'
  } finally { loading.value = false }
}

async function deleteDoc(sourceId: string) {
  if (!confirm('Удалить документ и все его чанки?')) return
  try {
    await $fetch(`${api}/rag/documents/${sourceId}`, { method: 'DELETE', headers: authHeaders() })
    await loadDocuments()
  } catch (e: any) {
    uploadError.value = e?.data?.detail || e?.message || 'Не удалось удалить документ'
  }
}

onMounted(async () => {
  await loadDocuments()
  const savedJobId = localStorage.getItem('lb-active-job')
  if (savedJobId) { uploading.value = true; pollJob(savedJobId) }
})
</script>

<style scoped>
.admin-input {
  padding: 8px 12px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
}
.admin-input:focus { border-color: var(--accent); }

.spinner {
  width: 13px; height: 13px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
