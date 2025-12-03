<!-- presentation/frontend/src/views/CompanyChartsView.vue -->
<template>
  <section class="account-charts">
    <header class="account-charts__header">
      <h2>Gráficos de ratios por empresa</h2>

      <p v-if="companies.length">
        Companhias selecionadas:
        <strong>
          {{ companies.map((c) => `${c.company} (${c.ticker})`).join(' · ') }}
        </strong>
      </p>
      <p v-else class="muted">
        Nenhuma companhia selecionada. Use a Home para escolher e clique em
        “Visualizar Gráficos”.
      </p>

      <p class="muted">
        Exibindo as contas:
        {{ selectedAccounts.join(', ') }}.
      </p>
    </header>

    <main class="account-charts__body">
      <div v-if="chartsStore.isLoading" role="status" aria-live="polite">
        Carregando gráficos...
      </div>

      <div v-else-if="chartsStore.error" role="alert">
        {{ chartsStore.error }}
      </div>

      <div v-else-if="hasCharts">
        <section
          v-for="accountCode in selectedAccounts"
          :key="accountCode"
          class="account-charts__chart-block"
        >
          <h3 class="account-charts__chart-title">
            Conta {{ accountCode }}
          </h3>

          <PlotlyViewer
            :chart="chartsStore.chartsByAccount[accountCode]"
            :isLoading="chartsStore.isLoading"
            :error="chartsStore.error"
            :aria-label="`Gráfico da conta ${accountCode} para as companhias selecionadas`"
          />
        </section>
      </div>

      <div v-else class="muted">
        Selecione companhias na Home e clique em “Visualizar Gráficos” para
        carregar os dados.
      </div>
    </main>
  </section>
</template>

<script setup>
import { computed, watch } from 'vue'
import { storeToRefs } from 'pinia'

import PlotlyViewer from '../components/PlotlyViewer.vue'
import { useAccountChartsStore } from '../store/accountChartsStore'
import { useCompanyStore } from '../store/companyStore'

const chartsStore = useAccountChartsStore()
const companyStore = useCompanyStore()

const { filterQuery } = storeToRefs(companyStore)
const { companies, selectedAccounts } = storeToRefs(chartsStore)

// Mantém o filtro estruturado sincronizado com a CompanyStore
watch(
  filterQuery,
  (query) => {
    chartsStore.setFilterFromFilterQuery(query)
  },
  { deep: true, immediate: true },
)

// Caso ninguém tenha setado contas ainda, usa defaults
const defaultAccounts = ['02.03', '03.01', '03.11']
if (!selectedAccounts.value.length) {
  chartsStore.setSelectedAccounts(defaultAccounts)
}

const hasCharts = computed(() => {
  const charts = chartsStore.chartsByAccount || {}
  return Object.keys(charts).length > 0
})
</script>

<style scoped>
.account-charts {
  display: grid;
  gap: 1.5rem;
  padding: 1rem;
}

.account-charts__header {
  display: grid;
  gap: 0.75rem;
}

.account-charts__body {
  min-height: 280px;
}

.account-charts__chart-block {
  margin-bottom: 2rem;
}

.account-charts__chart-title {
  margin-bottom: 0.5rem;
  font-size: 1.05rem;
}

.muted {
  color: #64748b;
  font-size: 0.95rem;
}
</style>
