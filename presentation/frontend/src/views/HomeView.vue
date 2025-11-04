<template>
  <main class="home">
    <h1>{{ title }}</h1>
    <ChartSelector />
    <PlotlyViewer />
  </main>
</template>

<script setup>
import ChartSelector from '../components/ChartSelector.vue'
import PlotlyViewer from '../components/PlotlyViewer.vue'
import { computed } from 'vue'
import { useChartStore } from '../store/chartStore'

const store = useChartStore()
const title = computed(() => store.chart?.title || 'Charts FLY')
</script>
