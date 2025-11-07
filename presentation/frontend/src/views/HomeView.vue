<template>
  <main class="home">
    <section class="home__charts">
      <h1>{{ title }}</h1>
      <ChartSelector />
      <PlotlyViewer />
    </section>
    <CompanySearchBuilder class="home__search" />
  </main>
</template>

<script setup>
import { ref } from 'vue'
import ChartSelector from '../components/ChartSelector.vue'
import PlotlyViewer from '../components/PlotlyViewer.vue'
import CompanySearchBuilder from '../components/CompanySearchBuilder.vue'

const title = ref('Dashboard de Indicadores')
</script>

<style scoped>
.home {
  display: grid;
  gap: 2rem;
  padding: 1rem;
}

.home__charts {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.home__search {
  max-width: 100%;
}
</style>
