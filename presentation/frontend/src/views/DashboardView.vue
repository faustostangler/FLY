<template>
  <main class="dashboard">
    <h1>Dashboard FLY</h1>
    <ChartSelector />

    <PlotlyViewer />
  </main>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useChartStore } from "../stores/chartStore";
import ChartSelector from "../components/ChartSelector.vue";
import PlotlyViewer from "../components/PlotlyViewer.vue";

const store = useChartStore();

onMounted(() => {
  // Carrega o gráfico inicial ao abrir a página
  store.loadChart();
});
</script>

<style scoped>
.dashboard {
  max-width: 960px;
  margin: 0 auto;
  padding: 1rem;
}
</style>
