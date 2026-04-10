<template>
  <div class="h-full overflow-y-auto bg-canvas px-6 py-8">
    <div class="max-w-[840px] mx-auto flex flex-col gap-6">
      <h1 class="text-2xl font-bold text-ink">Анализ рекламных материалов</h1>
      <p class="text-[15px] text-ink-muted -mt-2">
        Загрузите рекламный текст или файл для проверки на соответствие законодательству РФ
      </p>

      <!-- Input card -->
      <div class="bg-panel border border-rim rounded-xl p-6 flex flex-col gap-4">

        <!-- Text input -->
        <div class="flex flex-col gap-1.5">
          <label class="text-sm font-medium text-ink-muted">Рекламный текст</label>
          <textarea
            v-model="inputText"
            rows="6"
            class="w-full bg-field border border-rim rounded-lg px-3 py-2.5 text-sm text-ink placeholder:text-ink-faint resize-y focus:outline-none focus:border-brand transition-colors"
            placeholder="Вставьте текст рекламного материала..."
            :disabled="analyzing"
          />
        </div>

        <!-- OR divider -->
        <div class="flex items-center gap-3 text-[12px] text-ink-faint">
          <div class="flex-1 border-t border-rim-faint" />
          <span>или загрузите файл</span>
          <div class="flex-1 border-t border-rim-faint" />
        </div>

        <!-- File upload -->
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

        <!-- Submit -->
        <button
          class="self-end px-5 py-2.5 rounded-lg text-sm font-semibold transition-all cursor-pointer"
          :class="canSubmit
            ? 'bg-brand text-white hover:bg-brand-lit'
            : 'bg-raised text-ink-faint cursor-not-allowed'"
          :disabled="!canSubmit"
          @click="runAnalysis"
        >
          <span v-if="analyzing" class="flex items-center gap-2">
            <svg class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <circle cx="12" cy="12" r="10" stroke-dasharray="31.4" stroke-dashoffset="10"/>
            </svg>
            Анализирую...
          </span>
          <span v-else>Анализировать</span>
        </button>
      </div>

      <!-- Thinking progress -->
      <ThinkingBlock
        v-if="thinking.length"
        :steps="thinking"
        :is-streaming="analyzing"
        :citations-count="citations.length"
      />

      <!-- Error -->
      <div v-if="error" class="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-[14px] text-red-400">
        {{ error }}
      </div>

      <!-- Results -->
      <template v-if="result">
        <!-- Overall summary -->
        <div class="bg-panel border border-rim rounded-xl p-5 flex flex-col gap-3">
          <div class="flex items-center gap-2.5">
            <span class="text-base font-semibold text-ink">Результат анализа</span>
            <span
              class="text-[11px] font-bold uppercase px-2 py-0.5 rounded"
              :class="overallBadgeClass"
            >
              {{ overallLabel }}
            </span>
          </div>
          <p class="text-sm leading-relaxed text-ink-muted">{{ result.summary }}</p>
        </div>

        <!-- Risks -->
        <div v-if="result.risks?.length" class="flex flex-col gap-3">
          <h2 class="text-base font-semibold text-ink">
            Выявленные риски ({{ result.risks.length }})
          </h2>
          <RiskCard v-for="(risk, i) in result.risks" :key="i" :risk="risk" />
        </div>

        <!-- No risks -->
        <div v-else class="bg-ok/10 border border-ok/30 rounded-lg px-4 py-3 text-[14px] text-green-400">
          Нарушений не выявлено. Материал соответствует законодательству.
        </div>

        <!-- Citations -->
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
