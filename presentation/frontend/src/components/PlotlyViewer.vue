<template>
  <section class="plotly-viewer">
    <div v-if="resolvedIsLoading" role="status" aria-live="polite">
      Carregando gráfico...
    </div>

    <div v-else-if="resolvedError" role="alert">
      {{ resolvedError }}
    </div>

    <div
      v-else-if="resolvedChart"
      role="img"
      :aria-label="resolvedAriaLabel"
    >
      <VuePlotly
        :data="resolvedChart.data"
        :layout="resolvedChart.layout"
        :useResizeHandler="true"
        style="width: 100%; height: 400px;"
      />
    </div>

    <p v-else>
      Selecione uma companhia para visualizar o gráfico.
    </p>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { VuePlotly } from 'vue3-plotly'
import { useChartStore } from '../store/chartStore'

const props = defineProps({
  chart: {
    type: Object,
    default: null,
  },
  isLoading: {
    type: Boolean,
    default: undefined,
  },
  error: {
    type: String,
    default: undefined,
  },
})

const store = useChartStore()

// valores do store (para compatibilidade com telas antigas que não passam props)
const storeChart = computed(() => store.chart)
const storeIsLoading = computed(() => store.isLoading)
const storeError = computed(() => store.error)

// resolução de fonte: se a prop vier, usa a prop; caso contrário, usa o store
const resolvedChart = computed(() =>
  props.chart !== null ? props.chart : storeChart.value,
)

const resolvedIsLoading = computed(() =>
  typeof props.isLoading === 'boolean'
    ? props.isLoading
    : storeIsLoading.value,
)

const resolvedError = computed(() =>
  typeof props.error === 'string'
    ? props.error
    : storeError.value,
)

const resolvedAriaLabel = computed(() => {
  const chart = resolvedChart.value
  if (!chart) {
    return 'Gráfico'
  }
  const title = chart.layout?.title
  if (typeof title === 'string') {
    return title
  }
  if (title && typeof title.text === 'string') {
    return title.text
  }
  return 'Gráfico'
})
</script>
