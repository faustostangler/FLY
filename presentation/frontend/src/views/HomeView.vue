<template>
  <main class="home">
    <CompanySearchBuilder class="home__search" />

    <section class="home__charts">
      <h2>{{ title }}</h2>

      <CompanySelectionSummary />

      <section class="home__charts-results" aria-labelledby="chart-results-heading">
        <h2 id="chart-results-heading">Resultados</h2>

        <ChartSelector />
        <PlotlyViewer title="Preço" />
      </section>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import ChartSelector from '../components/ChartSelector.vue'
import PlotlyViewer from '../components/PlotlyViewer.vue'
import CompanySearchBuilder from '../components/CompanySearchBuilder.vue'
import CompanySelectionSummary from '../components/CompanySelectionSummary.vue'

const title = ref('Dashboard de indicadores')
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding: 1rem;
}

.home__charts {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.home__charts-results {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1rem;
}

.home__search {
  max-width: 100%;
}
</style>
