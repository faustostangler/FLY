<template>
  <main class="home">
    <h1>{{ title }}</h1>
    <ChartSelector />
    <PlotlyViewer />
  </main>
</template>

<script setup>
import ChartSelector from '../components/ChartSelector.vue'
</script>
