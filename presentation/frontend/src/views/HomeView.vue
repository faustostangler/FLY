<template>
  <main class="home">
    <CompanySearchBuilder class="home__search" />

    <section class="home__charts">
      <h2>{{ title }}</h2>

      <CompanySelectionSummary />

      <section
        v-if="selectedPairs.length"
        class="home__selected-companies"
        aria-labelledby="selected-companies-heading"
      >
        <h3 id="selected-companies-heading">Empresas selecionadas</h3>

        <table class="home__selected-table">
          <thead>
            <tr>
              <th scope="col">Companhia</th>
              <th scope="col">Ticker</th>
              <th scope="col" class="home__selected-actions">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="pair in selectedPairs"
              :key="`${pair.company}::${pair.ticker}`"
            >
              <td>{{ pair.company }}</td>
              <td>{{ pair.ticker }}</td>
              <td class="home__selected-actions">
                <button
                  type="button"
                  class="home__charts-button"
                  @click="viewAccountCharts(pair)"
                >
                  Ver gráficos de ratios
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section
        class="home__charts-results"
        aria-labelledby="chart-results-heading"
      >
        <h2 id="chart-results-heading">Resultados</h2>
        <h3>Preço</h3>

        <PlotlyViewer />
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import PlotlyViewer from '../components/PlotlyViewer.vue'
import CompanySearchBuilder from '../components/CompanySearchBuilder.vue'
import CompanySelectionSummary from '../components/CompanySelectionSummary.vue'
import { useCompanyStore } from '../store/companyStore'

const title = ref('Dashboard de Indicadores')

const router = useRouter()
const companyStore = useCompanyStore()
const { selectedPairs: selectedPairsRef } = storeToRefs(companyStore)

const selectedPairs = computed(() => {
  const pairs = selectedPairsRef.value
  return Array.isArray(pairs) ? pairs : []
})

function viewAccountCharts(pair) {
  const company = String(pair?.company || '').trim()
  if (!company) {
    return
  }

  router.push({
    name: 'account-charts',
    query: {
      company,
    },
  })
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

.home__selected-companies {
  display: grid;
  gap: 0.75rem;
}

.home__selected-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
}

.home__selected-table th,
.home__selected-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.home__selected-table tbody tr:last-child td {
  border-bottom: none;
}

.home__charts-button {
  padding: 0.5rem 1rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.home__charts-button:hover,
.home__charts-button:focus-visible {
  background: #1d4ed8;
}

.home__charts-button:focus-visible {
  outline: 2px solid #1d4ed8;
  outline-offset: 2px;
}

.home__selected-actions {
  text-align: right;
}
</style>
