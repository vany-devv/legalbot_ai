<template>
  <div class="h-full flex flex-col bg-canvas overflow-hidden">

    <div class="progress-track flex-shrink-0 h-[2px] overflow-hidden" :class="analyzing ? 'opacity-100' : 'opacity-0'">
      <div class="progress-bar h-full bg-brand" />
    </div>

    <div class="flex-1 overflow-y-auto px-6 py-8">
      <div class="max-w-[840px] mx-auto flex flex-col gap-6">

        <Transition name="card-collapse">
          <div v-if="!hasStarted">
            <h1 class="text-2xl font-bold text-ink mb-1.5">Анализ рекламных материалов</h1>
            <p class="text-[15px] text-ink-muted">
              Загрузите рекламный текст или файл для проверки на соответствие законодательству РФ
            </p>
          </div>
        </Transition>

        <Transition name="card-collapse">
          <div v-if="!hasStarted" class="bg-panel border border-rim rounded-xl p-6 flex flex-col gap-4">
            <div class="flex flex-col gap-1.5">
              <label class="text-sm font-medium text-ink-muted">Рекламный текст</label>
              <textarea
                v-model="inputText"
                rows="6"
                class="w-full bg-field border border-rim rounded-lg px-3 py-2.5 text-sm text-ink placeholder:text-ink-faint resize-y focus:outline-none focus:border-brand transition-colors"
                placeholder="Вставьте текст рекламного материала..."
              />
            </div>

            <div class="flex items-center gap-3 text-[12px] text-ink-faint">
              <div class="flex-1 border-t border-rim" />
              <span>или загрузите файл</span>
              <div class="flex-1 border-t border-rim" />
            </div>

            <div
              class="dropzone flex flex-col items-center gap-2 py-5 px-6 border-2 border-dashed rounded-lg cursor-pointer transition-all text-sm"
              :class="dragging
                ? 'border-brand bg-brand-dim text-ink-muted'
                : uploadFile
                  ? 'border-ok bg-ok/5 text-ink'
                  : 'border-rim text-ink-faint hover:border-brand hover:bg-brand-dim hover:text-ink-muted'"
              @dragover.prevent="dragging = true"
              @dragleave.prevent="dragging = false"
              @drop.prevent="onDrop"
              @click="fileInput?.click()"
            >
              <input ref="fileInput" type="file" accept=".pdf,.docx,.txt" class="hidden" @change="onFileChange" />
              <template v-if="uploadFile">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-ok">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                </svg>
                <span class="font-medium text-sm">{{ uploadFile.name }}</span>
                <button class="text-xs text-danger hover:underline" @click.stop="uploadFile = null">Удалить</button>
              </template>
              <template v-else>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <span>PDF, DOCX или TXT</span>
              </template>
            </div>

            <button
              class="self-end px-5 py-2.5 rounded-lg text-sm font-semibold transition-all cursor-pointer"
              :class="canSubmit ? 'bg-brand text-white hover:bg-brand-lit' : 'bg-raised text-ink-faint cursor-not-allowed'"
              :disabled="!canSubmit"
              @click="runAnalysis"
            >
              Анализировать
            </button>
          </div>
        </Transition>

        <ThinkingBlock
          v-if="thinking.length"
          :steps="thinking"
          :is-streaming="analyzing"
          :citations-count="citations.length"
        />

        <div v-if="error" class="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-400">
          {{ error }}
        </div>

        <template v-if="result">
          <div class="bg-panel border border-rim rounded-xl p-5 flex flex-col gap-3">
            <div class="flex items-center justify-between gap-3">
              <div class="flex items-center gap-2.5">
                <span class="text-base font-semibold text-ink">Результат анализа</span>
                <span class="text-[11px] font-bold uppercase px-2 py-0.5 rounded" :class="overallBadgeClass">
                  {{ overallLabel }}
                </span>
              </div>
              <button
                class="text-xs text-ink-faint hover:text-ink border border-rim hover:border-ink-faint px-3 py-1.5 rounded-lg transition-colors cursor-pointer flex-shrink-0"
                @click="startOver"
              >
                Новый анализ
              </button>
            </div>
            <p class="text-sm leading-relaxed text-ink-muted">{{ result.summary }}</p>
          </div>

          <div v-if="result.risks?.length" class="flex flex-col gap-3">
            <h2 class="text-base font-semibold text-ink">Выявленные риски ({{ result.risks.length }})</h2>
            <RiskCard v-for="(risk, i) in result.risks" :key="i" :risk="risk" />
          </div>

          <div v-else class="bg-ok/10 border border-ok/30 rounded-lg px-4 py-3 text-sm text-green-400">
            Нарушений не выявлено. Материал соответствует законодательству.
          </div>

          <div v-if="citations.length" class="flex flex-col gap-2">
            <button
              class="flex items-center gap-1.5 text-[11px] font-semibold text-ink-faint uppercase tracking-wider hover:text-ink-muted transition-colors cursor-pointer select-none"
              @click="citationsOpen = !citationsOpen"
            >
              <svg
                width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                class="transition-transform duration-150 flex-shrink-0"
                :class="citationsOpen ? 'rotate-0' : '-rotate-90'"
              >
                <polyline points="6 9 12 15 18 9"/>
              </svg>
              Источники ({{ citations.length }})
            </button>
            <div v-if="citationsOpen" class="grid gap-1.5">
              <CitationCard v-for="c in citations" :key="c.id" :citation="c" />
            </div>
          </div>
        </template>

      </div>
    </div>

    <Transition name="bar-slide">
      <div v-if="hasStarted" class="flex-shrink-0 border-t border-rim bg-canvas">
        <div class="px-6 pb-4 pt-3 max-w-[840px] mx-auto w-full">
          <Transition name="chip-slide">
            <div v-if="barFile" class="mb-2 flex items-center gap-1.5">
              <div class="flex items-center gap-1.5 px-2.5 py-1 bg-panel border border-rim rounded-full text-xs text-ink-muted">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-ok flex-shrink-0">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                </svg>
                <span class="truncate max-w-[200px]">{{ barFile.name }}</span>
                <button class="ml-0.5 text-ink-faint hover:text-danger transition-colors cursor-pointer" @click="barFile = null">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>
          </Transition>

          <div class="bar-wrap flex items-center gap-2 px-3 py-2.5 bg-field border border-rim rounded-2xl transition-colors">
            <button
              class="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-xl text-ink-faint hover:text-ink hover:bg-dimmed transition-colors cursor-pointer"
              title="Прикрепить файл"
              :disabled="analyzing"
              @click="barFileInput?.click()"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
            </button>
            <input ref="barFileInput" type="file" accept=".pdf,.docx,.txt" class="hidden" @change="onBarFileChange" />

            <textarea
              ref="barTextareaRef"
              v-model="barText"
              class="flex-1 bg-transparent text-ink text-base leading-relaxed resize-none outline-none max-h-[140px] placeholder-ink-faint"
              placeholder="Новый материал для анализа..."
              rows="1"
              :disabled="analyzing"
              @keydown.enter.exact.prevent="runBarAnalysis"
              @input="autoResizeBar"
            />

            <button
              class="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-xl bg-brand text-white cursor-pointer transition-all hover:bg-brand-lit disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!canBarSubmit"
              @click="runBarAnalysis"
            >
              <svg v-if="analyzing" class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="10" stroke-dasharray="31.4" stroke-dashoffset="10"/>
              </svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<script setup lang="ts">
useHead({ title: 'Анализ рекламы' })

const { thinking, citations, result, analyzing, error, analyze, reset } = useAnalyze()

const inputText = ref('')
const uploadFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement>()
const dragging = ref(false)
const citationsOpen = ref(false)

const canSubmit = computed(() => !analyzing.value && (inputText.value.trim() || uploadFile.value))
const hasStarted = computed(() => analyzing.value || !!result.value || !!error.value)

const barText = ref('')
const barFile = ref<File | null>(null)
const barFileInput = ref<HTMLInputElement>()
const barTextareaRef = ref<HTMLTextAreaElement | null>(null)

const canBarSubmit = computed(() => !analyzing.value && (barText.value.trim() || barFile.value))

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.[0]) uploadFile.value = target.files[0]
}

function onDrop(e: DragEvent) {
  dragging.value = false
  if (e.dataTransfer?.files?.[0]) uploadFile.value = e.dataTransfer.files[0]
}

async function runAnalysis() {
  if (!canSubmit.value) return
  citationsOpen.value = false
  await analyze(inputText.value || null, uploadFile.value, 10)
}

function onBarFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.[0]) barFile.value = target.files[0]
}

async function runBarAnalysis() {
  if (!canBarSubmit.value) return
  const text = barText.value
  const file = barFile.value
  barText.value = ''
  barFile.value = null
  citationsOpen.value = false
  reset()
  await nextTick()
  inputText.value = text
  uploadFile.value = file
  await analyze(text || null, file, 10)
}

function startOver() {
  reset()
  inputText.value = ''
  uploadFile.value = null
  barText.value = ''
  barFile.value = null
}

function autoResizeBar() {
  const el = barTextareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 140) + 'px'
}

const overallLabel = computed(() => {
  switch (result.value?.overall_risk_level) {
    case 'high': return 'Высокий риск'
    case 'medium': return 'Средний риск'
    case 'low': return 'Низкий риск'
    case 'none': return 'Без рисков'
    default: return result.value?.overall_risk_level || ''
  }
})

const overallBadgeClass = computed(() => {
  switch (result.value?.overall_risk_level) {
    case 'high': return 'bg-red-500/15 text-red-400'
    case 'medium': return 'bg-amber-500/15 text-amber-400'
    case 'low': return 'bg-yellow-500/15 text-yellow-400'
    case 'none': return 'bg-green-500/15 text-green-400'
    default: return 'bg-raised text-ink-faint'
  }
})
</script>

<style scoped>
.card-collapse-enter-active { transition: opacity 0.22s ease, transform 0.22s ease; }
.card-collapse-leave-active  { transition: opacity 0.16s ease, transform 0.16s ease; }
.card-collapse-enter-from,
.card-collapse-leave-to      { opacity: 0; transform: translateY(-8px); }

.bar-slide-enter-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.bar-slide-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.bar-slide-enter-from,
.bar-slide-leave-to     { opacity: 0; transform: translateY(12px); }

.chip-slide-enter-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.chip-slide-leave-active { transition: opacity 0.1s ease, transform 0.1s ease; }
.chip-slide-enter-from,
.chip-slide-leave-to     { opacity: 0; transform: translateY(4px); }

.bar-wrap:focus-within { border-color: var(--accent); }

.progress-track { background: transparent; transition: opacity 0.4s ease; }
.progress-bar {
  width: 40%;
  border-radius: 2px;
  animation: shimmer 1.4s ease-in-out infinite;
}
@keyframes shimmer {
  0%   { transform: translateX(-150%); }
  100% { transform: translateX(350%); }
}
</style>
