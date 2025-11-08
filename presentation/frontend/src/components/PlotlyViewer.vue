<template>
  <section class="plotly-viewer">
    <div v-if="isLoading" role="status" aria-live="polite">
      Carregando gráfico...
    </div>

    <div v-else-if="error" role="alert">
      {{ error }}
    </div>

    <div
      v-else-if="chart"
      role="img"
      :aria-label="chart.title"
    >
      <VuePlotly
        :data="chart.data"
        :layout="chart.layout"
        :useResizeHandler="true"
        style="width: 100%; height: 400px;"
      />
    </div>

    <p v-else>
      Nenhum gráfico carregado.
    </p>
  </section>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChartStore } from '../store/chartStore'
import { useCompanyStore } from '../store/companyStore'

const chartStore = useChartStore()
const companyStore = useCompanyStore()
const route = useRoute()
const router = useRouter()

const chart = computed(() => chartStore.chart)
const isLoading = computed(() => chartStore.isLoading)
const error = computed(() => chartStore.error)
const selectedTicker = computed(() => companyStore.selectedTicker)

function ensureTickerQuery(ticker) {
  if (!ticker) return
  const currentType = typeof route.query.type === 'string' ? route.query.type : undefined
  if (currentType === ticker) {
    return
  }
  router.replace({ query: { ...route.query, type: ticker } })
}

watch(
  selectedTicker,
  (ticker) => {
    if (!ticker) {
      return
    }
    ensureTickerQuery(ticker)
    chartStore.loadChartByTicker(ticker)
  },
)

watch(
  () => route.query.type,
  (value) => {
    const ticker = typeof value === 'string' ? value : ''
    if (ticker && ticker !== selectedTicker.value) {
      companyStore.setSelectedTicker(ticker)
    }
  },
  { immediate: true },
)

onMounted(() => {
  const queryTicker = typeof route.query.type === 'string' ? route.query.type : ''
  if (queryTicker) {
    if (queryTicker !== selectedTicker.value) {
      companyStore.setSelectedTicker(queryTicker)
    } else if (!chartStore.chart) {
      chartStore.loadChartByTicker(queryTicker)
    }
    return
  }

  const fallbackTicker =
    selectedTicker.value ||
    chartStore.params.type ||
    'PETR4'

  if (!fallbackTicker) {
    return
  }

  if (fallbackTicker !== selectedTicker.value) {
    companyStore.setSelectedTicker(fallbackTicker)
  } else if (!chartStore.chart) {
    chartStore.loadChartByTicker(fallbackTicker)
    ensureTickerQuery(fallbackTicker)
  }
})
</script>
