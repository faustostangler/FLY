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
      Selecione uma companhia para visualizar o gráfico.
    </p>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useChartStore } from '../store/chartStore'

const store = useChartStore()

const chart = computed(() => store.chart)
const isLoading = computed(() => store.isLoading)
const error = computed(() => store.error)
</script>
