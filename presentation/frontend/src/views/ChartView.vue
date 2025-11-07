<!-- src/views/ChartView.vue -->
<template>
  <section class="chart-view">
    <!-- 1) Selector de tipo de gráfico / símbolo -->
    <header class="chart-header">
      <h1>Gráfico</h1>
      <ChartSelector />
    </header>

    <!-- 2) Estado de loading -->
    <div v-if="isLoading" class="chart-loading">
      Carregando gráfico...
    </div>

    <!-- 3) Erro da API -->
    <div v-else-if="error" class="chart-error">
      {{ error }}
    </div>

    <!-- 4) Nenhum dado ainda -->
    <div v-else-if="!chart">
      Nenhum gráfico carregado ainda.
    </div>

    <!-- 5) Gráfico Plotly -->
    <div v-else class="chart-container">
      <VuePlotly
        :data="chart.data"
        :layout="chart.layout"
        :config="plotConfig"
      />
      <!-- Acessibilidade: descrição textual do gráfico -->
      <div
        role="img"
        aria-label="Gráfico de dados de mercado gerado a partir da API FLY"
      ></div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useChartStore } from '../store/chartStore'
import ChartSelector from '../components/ChartSelector.vue'

const store = useChartStore()
const { chart, isLoading, error, params } = storeToRefs(store)

// Config extra do Plotly (opcional)
const plotConfig = computed(() => ({
  responsive: true,
  displaylogo: false,
  // aqui você pode ajustar interações do Plotly se quiser
}))

// Quando a view carregar pela primeira vez, garante um gráfico inicial
onMounted(async () => {
  // só carrega se ainda não tiver gráfico
  if (!chart.value) {
    await store.loadChart()
  }
})
</script>

<style scoped>
.chart-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}

.chart-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.chart-container {
  min-height: 300px;
}

.chart-loading,
.chart-error {
  padding: 0.5rem;
}
</style>
