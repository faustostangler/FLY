<template>
  <section class="plotly-viewer" aria-labelledby="plotly-viewer-heading">
    <h3 id="plotly-viewer-heading">{{ props.title }}</h3>

    <div v-if="isLoading" class="plotly-viewer__status" role="status">
      Carregando gráfico...
    </div>

    <div v-else-if="error" class="plotly-viewer__status plotly-viewer__status--error" role="alert">
      {{ error }}
    </div>

    <div v-else-if="chart" class="plotly-viewer__chart" role="img" :aria-label="chart.title">
      <header class="plotly-viewer__chart-header">
        <h4>{{ chart.title }}</h4>
        <span class="plotly-viewer__badge">{{ activeTicker }}</span>
      </header>
      <ul>
        <li v-for="point in chart.series" :key="point.date">
          <span class="plotly-viewer__date">{{ point.date }}</span>
          <span class="plotly-viewer__value">{{ point.close.toFixed(2) }}</span>
        </li>
      </ul>
    </div>

    <p v-else class="plotly-viewer__status">Nenhum gráfico carregado.</p>
  </section>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChartStore } from '../store/chartStore'
import { useCompanyStore } from '../store/companyStore'

const props = defineProps({
  title: {
    type: String,
    default: 'Preço',
  },
})

const chartStore = useChartStore()
const companyStore = useCompanyStore()
const route = useRoute()
const router = useRouter()

const chart = computed(() => chartStore.chart)
const isLoading = computed(() => chartStore.isLoading)
const error = computed(() => chartStore.error)
const activeTicker = computed(() => companyStore.selectedTicker || chartStore.params.type)

function ensureTickerQuery(ticker) {
  if (!ticker) return
  const currentType = typeof route.query.type === 'string' ? route.query.type : undefined
  if (currentType === ticker) {
    return
  }
  router.replace({ query: { ...route.query, type: ticker } })
}

watch(
  () => companyStore.selectedTicker,
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
    if (ticker && ticker !== companyStore.selectedTicker) {
      companyStore.setSelectedTicker(ticker)
    }
  },
  { immediate: true },
)

onMounted(() => {
  const queryTicker = typeof route.query.type === 'string' ? route.query.type : ''
  if (queryTicker) {
    if (queryTicker !== companyStore.selectedTicker) {
      companyStore.setSelectedTicker(queryTicker)
    } else {
      chartStore.loadChartByTicker(queryTicker)
    }
    return
  }

  const fallbackTicker =
    companyStore.selectedTicker || chartStore.params.type || 'PETR4'

  if (!fallbackTicker) {
    return
  }

  if (fallbackTicker !== companyStore.selectedTicker) {
    companyStore.setSelectedTicker(fallbackTicker)
  } else {
    chartStore.loadChartByTicker(fallbackTicker)
  }

  ensureTickerQuery(fallbackTicker)
})
</script>

<style scoped>
.plotly-viewer {
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.plotly-viewer__status {
  color: #475569;
}

.plotly-viewer__status--error {
  color: #dc2626;
}

.plotly-viewer__chart {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.plotly-viewer__chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.plotly-viewer__badge {
  background: #0f172a;
  color: #fff;
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
  font-size: 0.75rem;
}

.plotly-viewer__chart ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.35rem;
}

.plotly-viewer__chart li {
  display: flex;
  justify-content: space-between;
  font-family: 'Roboto Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    'Liberation Mono', 'Courier New', monospace;
  font-size: 0.85rem;
  color: #0f172a;
}

.plotly-viewer__date {
  opacity: 0.7;
}

.plotly-viewer__value {
  font-weight: 600;
}
</style>
