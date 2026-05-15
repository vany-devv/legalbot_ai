<template>
  <div class="h-full flex flex-col bg-canvas overflow-hidden">

    <!-- Streaming progress -->
    <div class="progress-track flex-shrink-0 h-[2px] overflow-hidden" :class="analyzing ? 'opacity-100' : 'opacity-0'">
      <div class="progress-bar h-full bg-brand" />
    </div>

    <div class="flex-1 overflow-y-auto px-6 py-6">
      <div class="max-w-[1280px] mx-auto flex flex-col gap-5">

        <!-- ─── Header strip ─────────────────────────────────────── -->
        <div class="flex items-start sm:items-center justify-between gap-3 flex-wrap">
          <div class="flex items-center gap-3 min-w-0">
            <div class="flex items-center justify-center w-9 h-9 rounded-lg flex-shrink-0"
                 :style="{ background: 'var(--accent-subtle)', color: 'var(--accent)' }">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <div class="flex flex-col min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <h1 class="text-xl font-display font-bold tracking-tight text-ink leading-tight">Анализ рекламы</h1>
                <span class="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded"
                      :style="{ background: 'var(--accent-subtle)', color: 'var(--accent)' }">PRO</span>
              </div>
              <p class="text-[13px] text-ink-muted truncate">Проверка на соответствие рекламному законодательству</p>
            </div>
          </div>

          <div class="flex items-center gap-2 flex-shrink-0">
            <button
              v-if="result"
              class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rim text-sm text-ink-muted hover:text-ink hover:bg-dimmed transition-colors cursor-pointer"
              @click="exportPdf"
              :disabled="exporting"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              {{ exporting ? 'Подготовка...' : 'Экспорт PDF' }}
            </button>
            <button
              v-if="result"
              class="px-3 py-1.5 rounded-lg border border-rim text-sm text-ink-muted hover:text-ink hover:bg-dimmed transition-colors cursor-pointer"
              @click="startOver"
            >
              Новый анализ
            </button>
            <button
              v-if="result"
              class="hidden lg:flex items-center justify-center w-8 h-8 rounded-lg border border-rim text-ink-muted hover:text-ink hover:bg-dimmed transition-colors cursor-pointer"
              :title="sidebarOpen ? 'Скрыть панель' : 'Показать панель'"
              :aria-label="sidebarOpen ? 'Скрыть панель' : 'Показать панель'"
              @click="sidebarOpen = !sidebarOpen"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"
                   class="transition-transform duration-300"
                   :class="sidebarOpen ? '' : 'rotate-180'">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- ─── Initial form ─────────────────────────────────────── -->
        <Transition name="card-collapse">
          <div v-if="!hasStarted" class="max-w-[840px] mx-auto w-full flex flex-col gap-3">
            <p class="text-[14px] text-ink-muted">
              Загрузите рекламный текст или файл для проверки на соответствие законодательству РФ
            </p>
          </div>
        </Transition>

        <Transition name="card-collapse">
          <div v-if="!hasStarted" class="bg-panel border border-rim rounded-xl p-6 flex flex-col gap-4 max-w-[840px] mx-auto w-full">
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
                <span>PDF, DOCX или TXT — до 10 МБ</span>
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

        <!-- ─── REPORT (Workbench layout) ─────────────────────── -->
        <!-- Показываем как только пришёл ad_text — материал виден сразу, риски и
             правая колонка догружаются по мере streaming'а. -->
        <template v-if="analyzedText || result">
          <div class="flex flex-col lg:flex-row gap-5">

            <!-- LEFT column -->
            <div class="flex-1 min-w-0 flex flex-col gap-5">

              <!-- Material card — плавное появление когда придёт ad_text event -->
              <Transition name="material-fade" appear>
              <div class="bg-panel border border-rim rounded-xl overflow-hidden">
                <div class="flex items-center justify-between px-4 py-3 border-b border-rim-faint gap-3">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="text-[12px] font-semibold uppercase tracking-wider text-ink-faint flex-shrink-0">
                      Материал
                    </span>
                    <span v-if="materialTitle" class="text-[13px] text-ink truncate font-medium" :title="materialTitle">
                      · {{ materialTitle }}
                    </span>
                  </div>
                  <span class="text-[11px] text-ink-faint tabular-nums flex-shrink-0">
                    {{ analyzedText.length.toLocaleString('ru-RU') }} симв.
                  </span>
                </div>
                <div
                  class="material-content px-5 py-4 text-[14px] leading-[1.7] text-ink break-words"
                  v-html="annotatedHtml"
                  @click="onMaterialClick"
                />
              </div>
              </Transition>

              <!-- Severity filter chips -->
              <div v-if="result?.risks?.length" class="flex items-center gap-2 flex-wrap">
                <span class="text-[11px] font-semibold uppercase tracking-wider text-ink-faint mr-1">Найдено</span>
                <button
                  v-for="lvl in (['high','medium','low'] as const)"
                  :key="lvl"
                  v-show="riskCounts[lvl] > 0"
                  class="chip"
                  :class="[`chip-${lvl}`, severityFilter === lvl ? 'chip-active' : '']"
                  @click="severityFilter = severityFilter === lvl ? null : lvl"
                >
                  <strong class="font-bold">{{ riskCounts[lvl] }}</strong>
                  <span>{{ chipLabel(lvl, riskCounts[lvl]) }}</span>
                </button>
                <button
                  v-if="severityFilter"
                  class="text-[11px] text-ink-faint hover:text-ink underline-offset-2 hover:underline transition-colors cursor-pointer ml-1"
                  @click="severityFilter = null"
                >
                  сбросить
                </button>
              </div>

              <!-- Risks heading -->
              <div v-if="result?.risks?.length" class="flex items-center -mb-2">
                <span class="text-[11px] font-semibold uppercase tracking-wider text-ink-faint">Риски</span>
              </div>

              <!-- Risk cards -->
              <TransitionGroup
                v-if="filteredRisks.length"
                name="risk-list"
                tag="div"
                class="flex flex-col gap-3"
              >
                <div
                  v-for="(risk, i) in filteredRisks"
                  :key="`${risk.law_reference}-${risk.fragment}-${i}`"
                  :id="`risk-${result?.risks?.indexOf(risk) ?? i}`"
                  class="risk-card-wrap"
                >
                  <RiskCard
                    :risk="risk"
                    :idx="result?.risks?.indexOf(risk) ?? i"
                    @jump-to-fragment="onJumpToFragment"
                  />
                </div>
              </TransitionGroup>

              <!-- Empty filter result -->
              <div
                v-else-if="result?.risks?.length && severityFilter"
                class="text-[13px] text-ink-faint italic px-1"
              >
                Нет нарушений выбранного уровня.
              </div>

              <!-- No-violations state — только когда стрим успешно закончен и рисков
                   нет. Важно проверять `!error` — иначе при 402/413/network-failure
                   показывается ложное "Нарушений не выявлено", хотя анализ просто
                   не прошёл. Также требуем materialText (пришёл `ad_text` event) —
                   значит бэк реально что-то отдал, а не упал сразу. -->
              <div
                v-else-if="!analyzing && !error && materialText && !result?.risks?.length"
                class="bg-ok/10 border border-ok/30 rounded-lg px-4 py-4 text-sm text-ok flex items-center gap-2"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                <span>Нарушений не выявлено. Материал соответствует законодательству.</span>
              </div>
            </div>

            <!-- RIGHT column: collapsible sidebar.
                 Показываем ТОЛЬКО когда стрим закончен (есть summary/overall) или
                 citations пришли. Раньше гейт включал risks.length — это вызывало
                 преждевременный layout-shift: aside появлялся уже после первого
                 риска (отжимал материал на 320px), а контент score-card ещё ждал
                 result_meta. Теперь aside и его контент появляются синхронно. -->
            <Transition name="sidebar-slide">
              <aside
                v-if="sidebarOpen && (result?.summary || result?.overall_risk_level || citations.length)"
                class="lg:w-[320px] lg:flex-shrink-0 flex flex-col gap-4"
              >
                <!-- Score card — показываем только когда стрим закончен (пришёл
                     result_meta → есть summary/overall). Иначе цифра прыгала бы
                     при каждом push нового риска: "8.5 → 7.7 → 6.2..." -->
                <Transition name="score-pop">
                <div
                  v-if="result?.summary || result?.overall_risk_level"
                  class="bg-panel border border-rim rounded-xl p-5 flex flex-col gap-3 items-center text-center"
                >
                  <span class="text-[11px] font-semibold uppercase tracking-wider text-ink-faint">
                    Общая оценка
                  </span>
                  <div class="flex items-baseline gap-1.5">
                    <span
                      class="font-display font-bold leading-none tabular-nums tracking-tight"
                      style="font-size: 64px;"
                      :class="scoreColorClass"
                    >{{ scoreFormatted }}</span>
                  </div>
                  <span class="text-[11px] uppercase tracking-wider text-ink-faint">из 10</span>
                  <div
                    class="px-2.5 py-1 rounded-full text-[11px] font-semibold flex items-center gap-1.5"
                    :class="overallChipClass"
                  >
                    <svg v-if="result?.overall_risk_level !== 'none'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                      <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                    <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                    {{ overallLabel }}
                  </div>
                  <p v-if="result?.summary" class="text-[12px] leading-[1.55] text-ink-muted">
                    {{ result.summary }}
                  </p>
                </div>
                </Transition>

                <!-- Sources — группировка по (law, article).
                     Если статья разбита чанкером на N частей, юзер видит ОДНУ
                     карточку с заголовком статьи + меткой "(N частей)",
                     при разворачивании — последовательно все части. -->
                <div v-if="groupedCitations.length" class="bg-panel border border-rim rounded-xl p-4 flex flex-col gap-3">
                  <span class="text-[11px] font-semibold uppercase tracking-wider text-ink-faint">
                    Источники · {{ groupedCitations.length }}
                  </span>
                  <div class="flex flex-col gap-1">
                    <div v-for="(group, idx) in groupedCitations" :key="group.key" class="source-item">
                      <button
                        class="source-row w-full flex gap-2.5 items-start py-1.5 text-left transition-colors hover:bg-dimmed/40 rounded -mx-1 px-1 cursor-pointer"
                        @click="toggleSource(group.key)"
                      >
                        <span class="flex-shrink-0 w-5 h-5 rounded text-center text-[11px] leading-5 bg-raised text-ink-muted font-medium tabular-nums">
                          {{ idx + 1 }}
                        </span>
                        <div class="flex flex-col min-w-0 flex-1">
                          <span class="text-[12px] text-ink font-medium truncate">
                            {{ formatLaw(group.chunks[0]) }}
                            <span v-if="group.chunks.length > 1" class="text-ink-faint font-normal">
                              · {{ group.chunks.length }} ч.
                            </span>
                          </span>
                          <span class="text-[11px] text-ink-faint truncate">
                            {{ formatLawSub(group.chunks[0]) }}
                          </span>
                        </div>
                        <svg
                          width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
                          stroke-linecap="round" stroke-linejoin="round"
                          class="flex-shrink-0 mt-1.5 text-ink-faint transition-transform duration-200"
                          :class="expandedSources.has(group.key) ? 'rotate-180' : ''"
                        >
                          <polyline points="6 9 12 15 18 9"/>
                        </svg>
                      </button>
                      <Transition name="source-expand">
                        <div
                          v-if="expandedSources.has(group.key)"
                          class="ml-[26px] mt-1 mb-2 pl-3 border-l-2 border-rim text-[12px] leading-[1.55] text-ink-muted whitespace-pre-line"
                        >{{ groupText(group.chunks) }}</div>
                      </Transition>
                    </div>
                  </div>
                </div>
              </aside>
            </Transition>
          </div>
        </template>

      </div>
    </div>

    <!-- Bottom bar — re-analyze / new material -->
  </div>
</template>

<script setup lang="ts">
useHead({ title: 'Анализ рекламы' })

const { thinking, citations, result, analyzing, error, materialText, materialTitle, savedId, analyze, reset, abort } = useAnalyze()
const { currentId: currentAnalysisId } = useAnalysisHistory()
const route = useRoute()
const router = useRouter()

const inputText = ref('')
const uploadFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement>()
const dragging = ref(false)

const localText = ref('')
const analyzedText = computed(() => materialText.value || localText.value)

// Сбрасываем state на входе на эту страницу — иначе модульное состояние
// useAnalyze, заполненное на /analyze/:id через loadSaved(), просочится сюда
// и юзер увидит результат прошлого анализа вместо чистой формы.
onMounted(() => {
  reset()
  currentAnalysisId.value = null
})

const sidebarOpen = ref(true)
const severityFilter = ref<'high' | 'medium' | 'low' | null>(null)
const exporting = ref(false)
// Источники группируем по (law, article) — если статья разбита чанкером на
// несколько кусков, юзер видит одну карточку с раскрытием всех частей внутри,
// а не N отдельных карточек с одинаковым заголовком.
const groupedCitations = computed(() => {
  const groups = new Map<string, typeof citations.value extends readonly (infer T)[] ? T[] : never>()
  for (const c of citations.value) {
    const key = `${(c.meta as any)?.law ?? ''}|${(c.meta as any)?.article ?? ''}`
    if (!groups.has(key)) groups.set(key, [] as any)
    ;(groups.get(key) as any[]).push(c)
  }
  // Сортируем чанки внутри группы — сначала по chunk_index_in_article (если есть),
  // иначе по chunk_id для стабильности порядка.
  for (const list of groups.values()) {
    ;(list as any[]).sort((a: any, b: any) => {
      const ai = a.meta?.chunk_index_in_article
      const bi = b.meta?.chunk_index_in_article
      if (typeof ai === 'number' && typeof bi === 'number') return ai - bi
      return a.id < b.id ? -1 : 1
    })
  }
  return Array.from(groups.entries()).map(([key, chunks]) => ({ key, chunks: chunks as any[] }))
})

const expandedSources = ref<Set<string>>(new Set())

// Текст группы источника. Новые данные: бэк уже отдал склеенную статью одним
// чанком (length===1). Legacy сохранённые анализы: per-chunk citations —
// конкатенируем в один блок без "Часть N" (бэковая склейка к ним не применялась).
function groupText(chunks: any[]): string {
  if (chunks.length === 1) return chunks[0].quote || '—'
  return chunks.map(c => (c.quote || '').trim()).filter(Boolean).join('\n\n') || '—'
}

function toggleSource(key: string) {
  const s = new Set(expandedSources.value)
  if (s.has(key)) s.delete(key)
  else s.add(key)
  expandedSources.value = s
}

// Клик на карточке риска → скролл к подсвеченному фрагменту в тексте +
// мигание самого mark, чтобы юзер сразу увидел где это в материале.
function onJumpToFragment(idx: number) {
  // Если фильтр стоит, mark с этим idx всё равно в DOM (фильтр режет только
  // карточки, не подсветку), так что фильтр не трогаем.
  nextTick(() => {
    const marks = document.querySelectorAll(`.material-content mark[data-risk-idx="${idx}"]`)
    if (!marks.length) return
    ;(marks[0] as HTMLElement).scrollIntoView({ behavior: 'smooth', block: 'center' })
    marks.forEach(m => {
      const el = m as HTMLElement
      el.classList.remove('mark-flash')
      void el.offsetWidth
      el.classList.add('mark-flash')
      setTimeout(() => el.classList.remove('mark-flash'), 1500)
    })
  })
}

// Клик по подсвеченному фрагменту в тексте → скролл к карточке риска +
// короткая визуальная вспышка чтобы юзер сразу её заметил.
function onMaterialClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target?.classList?.contains('risk-mark')) return
  const idxStr = target.getAttribute('data-risk-idx')
  if (idxStr === null) return
  const idx = Number(idxStr)
  if (!Number.isInteger(idx)) return

  // Если активен severity-фильтр и нужная карточка скрыта — сбрасываем фильтр.
  const targetRisk = result.value?.risks?.[idx]
  if (targetRisk && severityFilter.value && targetRisk.risk_level !== severityFilter.value) {
    severityFilter.value = null
  }

  nextTick(() => {
    const el = document.getElementById(`risk-${idx}`)
    if (!el) return
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.remove('risk-card-flash')
    void el.offsetWidth  // force reflow чтобы анимация запустилась повторно
    el.classList.add('risk-card-flash')
    setTimeout(() => el.classList.remove('risk-card-flash'), 1500)
  })
}

const canSubmit = computed(() => !analyzing.value && (inputText.value.trim() || uploadFile.value))
const hasStarted = computed(() => analyzing.value || !!result.value || !!error.value)

const MAX_FILE_BYTES = 10 * 1024 * 1024  // 10 МБ — должно совпадать с rag/MAX_UPLOAD_BYTES
const MAX_FILE_MB = MAX_FILE_BYTES / (1024 * 1024)

function validateFileSize(f: File): boolean {
  if (f.size > MAX_FILE_BYTES) {
    useToast().show(`Файл слишком большой. Максимум ${MAX_FILE_MB} МБ.`, 'error', 5000)
    return false
  }
  return true
}

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const f = target.files?.[0]
  if (f && validateFileSize(f)) uploadFile.value = f
  if (target) target.value = ''
}

function onDrop(e: DragEvent) {
  dragging.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f && validateFileSize(f)) uploadFile.value = f
}

async function runAnalysis() {
  if (!canSubmit.value) return
  severityFilter.value = null
  localText.value = inputText.value || (uploadFile.value ? `[Файл: ${uploadFile.value.name}]` : '')
  await analyze(inputText.value || null, uploadFile.value, 10)
}

function startOver() {
  reset()
  inputText.value = ''
  uploadFile.value = null
  localText.value = ''
  severityFilter.value = null
  currentAnalysisId.value = null
}

// После успешного анализа — переходим на страницу сохранённого результата.
watch(savedId, (id) => {
  if (id) {
    currentAnalysisId.value = id
    router.replace(`/analyze/${id}`)
  }
})

// Отменяем активный стрим при уходе со страницы — иначе он продолжит писать
// в модульный state и вылезет при возврате.
onBeforeUnmount(() => {
  if (analyzing.value) abort()
})

// ─── Risk counts / filtering ──────────────────────────────────
const riskCounts = computed(() => {
  const c = { high: 0, medium: 0, low: 0 }
  for (const r of result.value?.risks || []) {
    if (r.risk_level === 'high') c.high++
    else if (r.risk_level === 'medium') c.medium++
    else c.low++
  }
  return c
})

const filteredRisks = computed(() => {
  const all = result.value?.risks || []
  if (!severityFilter.value) return all
  return all.filter(r => r.risk_level === severityFilter.value)
})

function chipLabel(level: 'high' | 'medium' | 'low', n: number): string {
  const map = {
    high:   ['высокий', 'высоких', 'высоких'],
    medium: ['средний', 'средних', 'средних'],
    low:    ['низкий',  'низких',  'низких'],
  } as const
  return pluralize(n, map[level] as [string, string, string])
}

// ─── Score (10-point scale, derived from risks) ──────────────
const score = computed(() => {
  const c = riskCounts.value
  const raw = 10 - c.high * 1.5 - c.medium * 0.8 - c.low * 0.3
  return Math.max(0, Math.min(10, raw))
})
const scoreFormatted = computed(() => score.value.toFixed(1))
const scoreColorClass = computed(() => {
  const s = score.value
  if (s < 4) return 'text-danger'
  if (s < 6) return 'text-warning'
  if (s < 8) return 'text-yellow-400'
  return 'text-ok'
})

// ─── Overall label / chip ────────────────────────────────────
const overallLabel = computed(() => {
  switch (result.value?.overall_risk_level) {
    case 'high': return 'Высокий риск нарушений'
    case 'medium': return 'Средний риск нарушений'
    case 'low': return 'Низкий риск нарушений'
    case 'none': return 'Без нарушений'
    default: return result.value?.overall_risk_level || ''
  }
})
const overallChipClass = computed(() => {
  switch (result.value?.overall_risk_level) {
    case 'high':   return 'bg-red-500/15 text-red-400'
    case 'medium': return 'bg-amber-500/15 text-amber-400'
    case 'low':    return 'bg-yellow-500/15 text-yellow-500'
    case 'none':   return 'bg-green-500/15 text-green-400'
    default:       return 'bg-raised text-ink-faint'
  }
})

// ─── Sources formatting ──────────────────────────────────────
function formatLaw(c: any): string {
  return c.meta?.law_short || c.meta?.law || 'Источник'
}
function formatLawSub(c: any): string {
  const num = c.meta?.law_number || c.meta?.number || ''
  const article = c.meta?.article ? `ст. ${c.meta.article}` : ''
  const date = c.meta?.date || c.meta?.year || ''
  return [num && `№ ${num}`, article, date].filter(Boolean).join(' · ')
}

// ─── Export PDF (placeholder — print-to-PDF) ─────────────────
async function exportPdf() {
  if (exporting.value) return
  exporting.value = true
  try {
    await nextTick()
    window.print()
  } finally {
    exporting.value = false
  }
}

// ─── Helpers ────────────────────────────────────────────────
function pluralize(n: number, forms: [string, string, string]) {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return forms[0]
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return forms[1]
  return forms[2]
}

function escapeHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

/**
 * Строит whitespace-tolerant regex для фрагмента: токены через \s+,
 * пунктуация-границы (кавычки/тире/точки) опциональны.
 * Это покрывает случаи, когда LLM вернул фрагмент с другой типографикой,
 * чем в исходном тексте.
 */
function buildFragmentRegex(fragment: string): RegExp | null {
  const trimmed = fragment.trim()
  if (!trimmed) return null
  // LLM иногда:
  //  1) нормализует словоформы ("работал" → "работает")
  //  2) пропускает запятые/тире между словами фрагмента
  //  3) оборачивает фрагмент в «...» / "..."
  // Поэтому матчим по словам-префиксам (для русского хватает срезать 2 буквы),
  // а между токенами разрешаем ЛЮБЫЕ не-буквенные символы (пробелы, запятые,
  // тире, точки и т.п.) — это покрывает пунктуацию в исходном тексте.
  const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  // Из исходного фрагмента берём только буквенно-цифровые токены, всю пунктуацию
  // (включая обрамляющие кавычки и внутренние запятые) выкидываем.
  const tokens = (trimmed.match(/[\p{L}\p{N}]+/gu) || []).filter(Boolean)
  if (!tokens.length) return null
  try {
    const parts = tokens.map(t => {
      const escaped = escape(t)
      const isWord = /^[\p{L}]+$/u.test(t)
      // Не-буквенные токены (числа, символы) — точное совпадение.
      if (!isWord) return escaped
      // 1-2 символа (предлоги, союзы) — точное совпадение, иначе ложные срабатывания
      // на похожих коротких словах ("и" → "из", "ил" и т.п.).
      if (t.length <= 2) return escaped
      // 3-4 символа: матчим как префикс + до 3 букв окончания (вид → видом, виду).
      if (t.length <= 4) return `${escaped}\\p{L}{0,3}`
      // 5+: срезаем 2 буквы окончания и разрешаем 0-4 буквы хвоста
      // (надёжный → надёжным, имущества → имуществом).
      const stem = escape(t.slice(0, -2))
      return `${stem}\\p{L}{0,4}`
    })
    // Между токенами — любая последовательность НЕ букв/цифр (пробелы, запятые,
    // тире, кавычки и т.п.). Минимум один символ-разделитель.
    return new RegExp(parts.join('[^\\p{L}\\p{N}]+'), 'giu')
  } catch {
    return null
  }
}

type Span = { start: number; end: number; level: string; idx: number }

function annotateBlock(block: string, risks: Array<{ fragment: string; risk_level: string }>): string {
  if (!risks.length) return escapeHtml(block)
  const spans: Span[] = []

  risks.forEach((r, idx) => {
    const f = (r.fragment || '').trim()
    if (!f || f === '[отсутствует в материале]') return
    const re = buildFragmentRegex(f)
    if (!re) return
    let m: RegExpExecArray | null
    while ((m = re.exec(block)) !== null) {
      if (m[0].length === 0) { re.lastIndex++; continue }
      spans.push({ start: m.index, end: m.index + m[0].length, level: r.risk_level, idx })
    }
  })

  if (!spans.length) return escapeHtml(block)

  // Earliest, longest wins on overlap
  spans.sort((a, b) => a.start - b.start || b.end - a.end)
  const resolved: Span[] = []
  let cursor = 0
  for (const s of spans) {
    if (s.start < cursor) continue
    resolved.push(s)
    cursor = s.end
  }

  let out = ''
  let pos = 0
  for (const s of resolved) {
    out += escapeHtml(block.slice(pos, s.start))
    out += `<mark class="risk-mark risk-${s.level}" data-risk-idx="${s.idx}">${escapeHtml(block.slice(s.start, s.end))}</mark>`
    pos = s.end
  }
  out += escapeHtml(block.slice(pos))
  return out
}

/**
 * Рендерит материал как набор <p>-абзацев с inline-подсветкой
 * фрагментов риска (рамка + цветная заливка).
 */
const annotatedHtml = computed(() => {
  const text = analyzedText.value
  if (!text) return ''
  const risks = (result.value?.risks || []) as Array<{ fragment: string; risk_level: string }>

  // 1) Двойные \n — главный сигнал абзаца.
  // 2) Если их нет, пробуем одиночные \n.
  // 3) Если и одиночных нет, а текст длинный — режем по предложениям.
  let paragraphs: string[]
  if (/\n\s*\n/.test(text)) {
    paragraphs = text.split(/\n\s*\n/)
  } else if (text.includes('\n')) {
    paragraphs = text.split(/\n+/)
  } else if (text.length > 500) {
    paragraphs = splitBySentences(text, 280)
  } else {
    paragraphs = [text]
  }
  paragraphs = paragraphs.map(p => p.replace(/\s*\n\s*/g, ' ').trim()).filter(Boolean)
  if (!paragraphs.length) return ''

  return paragraphs.map(p => `<p>${annotateBlock(p, risks)}</p>`).join('')
})

function splitBySentences(text: string, target = 280): string[] {
  const sentences = text.split(/(?<=[.!?])\s+(?=[«"А-ЯЁA-Z])/)
  if (sentences.length <= 2) return [text]
  const chunks: string[] = []
  let buf: string[] = []
  let cur = 0
  for (const s of sentences) {
    buf.push(s)
    cur += s.length + 1
    if (cur >= target) {
      chunks.push(buf.join(' '))
      buf = []
      cur = 0
    }
  }
  if (buf.length) chunks.push(buf.join(' '))
  return chunks
}
</script>

<style scoped>
/* ─── Form / bar transitions ─────────────────────────────────── */
.card-collapse-enter-active { transition: opacity 0.22s ease, transform 0.22s ease; }
.card-collapse-leave-active  { transition: opacity 0.16s ease, transform 0.16s ease; }
.card-collapse-enter-from,
.card-collapse-leave-to      { opacity: 0; transform: translateY(-8px); }

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

/* ─── Sidebar slide ─────────────────────────────────────────── */
.sidebar-slide-enter-active {
  transition: opacity 240ms var(--ease-out, cubic-bezier(0.2, 0.7, 0.2, 1)),
              transform 280ms var(--ease-out, cubic-bezier(0.2, 0.7, 0.2, 1));
}
.sidebar-slide-leave-active {
  transition: opacity 180ms ease,
              transform 220ms var(--ease-out, cubic-bezier(0.2, 0.7, 0.2, 1));
}
.sidebar-slide-enter-from,
.sidebar-slide-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* ─── Risk-list TransitionGroup ─────────────────────────────── */
.risk-list-enter-active { transition: opacity 220ms ease, transform 220ms var(--ease-out, cubic-bezier(0.2, 0.7, 0.2, 1)); }
.risk-list-leave-active { transition: opacity 160ms ease, transform 160ms ease; position: absolute; }
.risk-list-enter-from,
.risk-list-leave-to     { opacity: 0; transform: translateY(-6px); }
.risk-list-move         { transition: transform 220ms var(--ease-out, cubic-bezier(0.2, 0.7, 0.2, 1)); }

/* ─── Severity chips ─────────────────────────────────────────── */
.chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  padding: 4px 11px;
  border-radius: 9999px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background-color 140ms ease, border-color 140ms ease, color 140ms ease, transform 100ms ease;
  white-space: nowrap;
  font-weight: 500;
}
.chip:hover { transform: translateY(-1px); }

.chip-high {
  background: color-mix(in oklab, var(--danger) 16%, transparent);
  color: var(--danger);
}
.chip-medium {
  background: color-mix(in oklab, var(--warning) 18%, transparent);
  color: var(--warning);
}
.chip-low {
  background: color-mix(in oklab, #CA8A04 20%, transparent);
  color: #CA8A04;
}

.chip-active.chip-high   { background: color-mix(in oklab, var(--danger) 26%, transparent);  border-color: color-mix(in oklab, var(--danger) 55%, transparent); }
.chip-active.chip-medium { background: color-mix(in oklab, var(--warning) 28%, transparent); border-color: color-mix(in oklab, var(--warning) 55%, transparent); }
.chip-active.chip-low    { background: color-mix(in oklab, #CA8A04 30%, transparent);        border-color: color-mix(in oklab, #CA8A04 55%, transparent); }

/* ─── Inline risk highlights — soft bg + colored underline ─── */
:deep(.risk-mark) {
  border: none;
  border-radius: 3px;
  padding: 1px 4px;
  margin: 0 -1px;
  color: var(--text-primary);
  text-decoration-line: underline;
  text-decoration-style: solid;
  text-decoration-thickness: 2px;
  text-underline-offset: 4px;
  cursor: pointer;
  transition: background-color 120ms ease, filter 120ms ease;
}

/* ─── Risk card target highlight (когда юзер кликнул на mark) ─── */
.risk-card-wrap { border-radius: 12px; transition: box-shadow 200ms ease; }
.risk-card-flash {
  animation: risk-flash 1.5s ease-out;
}
@keyframes risk-flash {
  0%   { box-shadow: 0 0 0 0 color-mix(in oklab, var(--accent) 60%, transparent); }
  30%  { box-shadow: 0 0 0 4px color-mix(in oklab, var(--accent) 35%, transparent); }
  100% { box-shadow: 0 0 0 0 transparent; }
}

/* ─── Mark target highlight (когда юзер кликнул на карточку риска) ─── */
:deep(.risk-mark.mark-flash) {
  animation: mark-flash 1.5s ease-out;
}
@keyframes mark-flash {
  0%   { background-color: color-mix(in oklab, var(--accent) 50%, transparent); }
  30%  { background-color: color-mix(in oklab, var(--accent) 35%, transparent); }
  100% { background-color: var(--mark-original-bg, transparent); }
}
:deep(.risk-mark.risk-high) {
  background: color-mix(in oklab, var(--danger) 12%, transparent);
  text-decoration-color: var(--danger);
}
:deep(.risk-mark.risk-medium) {
  background: color-mix(in oklab, var(--warning) 14%, transparent);
  text-decoration-color: var(--warning);
}
:deep(.risk-mark.risk-low) {
  background: color-mix(in oklab, #CA8A04 16%, transparent);
  text-decoration-color: #CA8A04;
}
:deep(.risk-mark:hover) { filter: brightness(1.05); }

/* ─── Material content typography ─────────────────────────────── */
.material-content :deep(p) {
  margin: 0 0 16px 0;
  line-height: 1.7;
}
.material-content :deep(p:last-child) { margin-bottom: 0; }

/* ─── Source expand animation ─────────────────────────────────── */
.source-expand-enter-active {
  transition: opacity 200ms ease, max-height 240ms var(--ease-out, cubic-bezier(0.2,0.7,0.2,1)),
              margin-top 200ms ease, margin-bottom 200ms ease, padding-top 200ms ease, padding-bottom 200ms ease;
  overflow: hidden;
  max-height: 600px;
}
.source-expand-leave-active {
  transition: opacity 140ms ease, max-height 200ms var(--ease-out, cubic-bezier(0.2,0.7,0.2,1)),
              margin-top 160ms ease, margin-bottom 160ms ease, padding-top 160ms ease, padding-bottom 160ms ease;
  overflow: hidden;
  max-height: 600px;
}
.source-expand-enter-from,
.source-expand-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  padding-top: 0;
  padding-bottom: 0;
}

/* ─── Material card entrance (по приходу ad_text event) ─── */
.material-fade-enter-active {
  transition: opacity 280ms var(--ease-out), transform 280ms var(--ease-out);
}
.material-fade-enter-from {
  opacity: 0;
  transform: scale(0.99) translateY(4px);
}

/* ─── Score card pop при окончании streaming.
   Только opacity + лёгкий translateY, без scale — scale на 320px-блоке давал
   ощутимое "моргание" при появлении одновременно с aside. */
.score-pop-enter-active {
  transition: opacity 260ms var(--ease-out), transform 260ms var(--ease-out);
}
.score-pop-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

/* ─── Print: hide chrome, expand content ─────────────────────── */
@media print {
  :deep(.app-shell) > :not(.main-area) { display: none !important; }
  .progress-track { display: none; }
}
</style>
