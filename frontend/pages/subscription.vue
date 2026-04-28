<template>
  <div class="h-full overflow-y-auto bg-canvas px-6 py-12">
    <div class="max-w-[880px] mx-auto text-center">
      <h1 class="text-3xl font-bold text-ink mb-2">Тарифные планы</h1>
      <p class="text-[16px] text-ink-muted mb-10">Выберите подходящий план для вашей работы</p>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8 text-left">

        <!-- Basic -->
        <div class="flex flex-col p-7 bg-panel border border-rim rounded-xl">
          <p class="text-xs font-semibold uppercase tracking-wider text-ink-faint mb-3">Бесплатно</p>
          <h2 class="text-xl font-bold text-ink mb-2">Базовый</h2>
          <div class="mb-5">
            <span class="text-3xl font-bold text-ink">0 ₽</span>
            <span class="text-sm text-ink-faint"> / мес</span>
          </div>
          <ul class="flex-1 space-y-2.5 mb-6">
            <li v-for="f in basicFeatures" :key="f" class="flex items-start gap-2 text-sm text-ink-muted">
              <span class="text-ok font-bold flex-shrink-0 mt-0.5">✓</span> {{ f }}
            </li>
          </ul>
          <button disabled class="w-full py-2.5 rounded-lg border border-rim bg-raised text-ink-muted text-sm font-medium cursor-default">
            Текущий план
          </button>
        </div>

        <!-- Pro (featured) -->
        <div class="flex flex-col p-7 bg-panel border-2 border-brand rounded-xl relative">
          <div class="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-brand text-white text-xs font-semibold rounded-full">
            Популярный
          </div>
          <p class="text-xs font-semibold uppercase tracking-wider text-brand mb-3">Профессиональный</p>
          <h2 class="text-xl font-bold text-ink mb-2">Профессиональный</h2>
          <div class="mb-5">
            <span class="text-3xl font-bold text-ink">1 990 ₽</span>
            <span class="text-sm text-ink-faint"> / мес</span>
          </div>
          <ul class="flex-1 space-y-2.5 mb-6">
            <li v-for="f in proFeatures" :key="f" class="flex items-start gap-2 text-sm text-ink-muted">
              <span class="text-ok font-bold flex-shrink-0 mt-0.5">✓</span> {{ f }}
            </li>
          </ul>
          <button disabled class="w-full py-2.5 rounded-lg bg-brand text-white text-sm font-semibold opacity-60 cursor-not-allowed">
            Скоро
          </button>
        </div>

        <!-- Enterprise -->
        <div class="flex flex-col p-7 bg-panel border border-rim rounded-xl">
          <p class="text-xs font-semibold uppercase tracking-wider text-ink-faint mb-3">Для команд</p>
          <h2 class="text-xl font-bold text-ink mb-2">Корпоративный</h2>
          <div class="mb-5">
            <span class="text-2xl font-bold text-ink">Договорная</span>
          </div>
          <ul class="flex-1 space-y-2.5 mb-6">
            <li v-for="f in enterpriseFeatures" :key="f" class="flex items-start gap-2 text-sm text-ink-muted">
              <span class="text-ok font-bold flex-shrink-0 mt-0.5">✓</span> {{ f }}
            </li>
          </ul>
          <button disabled class="w-full py-2.5 rounded-lg bg-brand text-white text-sm font-semibold opacity-60 cursor-not-allowed">
            Связаться
          </button>
        </div>
      </div>

      <p class="text-sm text-ink-faint">
        Оплата временно недоступна. Функционал подписок находится в разработке.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
useHead({ title: 'Тарифы' })

const basicFeatures = ['10 запросов в день', 'Базовая модель LLM', 'Поиск по загруженным документам']
const proFeatures = ['Безлимитные запросы', 'Продвинутая модель LLM', 'Приоритетная обработка', 'История диалогов', 'Экспорт ответов']
const enterpriseFeatures = ['Все из «Профессионального»', 'Выделенный сервер', 'Интеграция с внутренними системами', 'SLA и техподдержка', 'Обучение на ваших документах']
</script>
