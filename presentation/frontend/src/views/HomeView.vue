<template>
  <main class="home">
    <section id=CompanySearchBuilder class="home__search">
      <CompanySearchBuilder />
    </section>

    <section id="CompanySelectionSummary" class="home__charts">
        <h2>{{ title }}</h2>
        <CompanySelectionSummary
          :selected-pairs="selectedPairs"
          @visualizar-graficos="onVisualizarGraficos"
        />
    </section>

    <section id="CompanyChartsView" class="home__charts-results">
      <h2>Resultados</h2>
        <div v-if="selectedPairs.length" aria-labelledby="chart-results-heading">
            <CompanyChartsView />
        </div>
        <div v-else class="home__charts-empty">
          Selecione uma ou mais companhias e clique em “Visualizar Gráficos”.
        </div>
    </section>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'

import CompanySearchBuilder from '../components/CompanySearchBuilder.vue'
import CompanySelectionSummary from '../components/CompanySelectionSummary.vue'
import CompanyChartsView from './CompanyChartsView.vue'

import { useCompanyStore } from '../store/companyStore'
import { useAccountChartsStore } from '../store/accountChartsStore'

const title = ref('Dashboard de Indicadores')

const companyStore = useCompanyStore()
const { selectedPairs: selectedPairsRef } = storeToRefs(companyStore)
const selectedPairs = computed(() => {
  const pairs = selectedPairsRef.value
  return Array.isArray(pairs) ? pairs : []
})

const chartsStore = useAccountChartsStore()
const onVisualizarGraficos = () => {
  chartsStore.setCompanies(selectedPairs.value)
  chartsStore.setSelectedAccounts(['02.03', '03.01', '03.11'])
  chartsStore.loadCharts()
}
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
  gap: 1.5rem;
  background-color: #a3c6f1;
  border-radius: 50px;
}

.home__charts-results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background-color: #d2f7c3;
  border-radius: 50px;
}

.home__search {
  max-width: 100%;
  background-color: #dde1e6;
  border-radius: 50px;
}

.home__charts-empty {
  color: #64748b;
}
</style>
