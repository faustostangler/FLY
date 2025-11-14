<template>
  <main class="home">
    <CompanySearchBuilder class="home__search" />

    <section class="home__charts">
      <h2>{{ title }}</h2>

      <CompanySelectionSummary />

      <SelectedCompaniesPanel
        :selected-pairs="selectedPairs"
        @visualizar-graficos="onVisualizarGraficos"
      />

      <section
        class="home__charts-results"
        aria-labelledby="chart-results-heading"
      >
        <h2 id="chart-results-heading">Resultados</h2>

        <AccountChartsView v-if="selectedPairs.length" />

        <p v-else class="home__charts-empty">
          Selecione uma ou mais companhias e clique em “Visualizar Gráficos”.
        </p>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'

import CompanySearchBuilder from '../components/CompanySearchBuilder.vue'
import CompanySelectionSummary from '../components/CompanySelectionSummary.vue'
import SelectedCompaniesPanel from '../components/SelectedCompaniesPanel.vue'
import AccountChartsView from './AccountChartsView.vue'

import { useCompanyStore } from '../store/companyStore'
import { useAccountChartsStore } from '../store/accountChartsStore'

const title = ref('Dashboard de Indicadores')

const companyStore = useCompanyStore()
const chartsStore = useAccountChartsStore()
const { selectedPairs: selectedPairsRef } = storeToRefs(companyStore)

const selectedPairs = computed(() => {
  const pairs = selectedPairsRef.value
  return Array.isArray(pairs) ? pairs : []
})

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
}

.home__charts-results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.home__search {
  max-width: 100%;
}

.home__charts-empty {
  color: #64748b;
}
</style>
