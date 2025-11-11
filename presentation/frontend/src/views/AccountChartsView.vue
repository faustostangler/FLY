<template>
  <section class="account-charts">
    <header class="account-charts__header">
      <h2>Gráficos de ratios por empresa</h2>

      <p v-if="activeCompanyName">
        Companhia selecionada:
        <strong>{{ activeCompanyName }}</strong>
      </p>
      <p v-else class="muted">
        Nenhuma companhia selecionada. Utilize os filtros na Home para escolher uma.
      </p>

      <p class="muted">
        Exibindo automaticamente 4 contas principais:
        02.03, 03.01, 04.02 e 05.01.
      </p>
    </header>

    <main class="account-charts__body">
      <div v-if="chartsStore.isLoading" role="status" aria-live="polite">
        Carregando gráficos de ratios...
      </div>

      <div v-else-if="chartsStore.error" role="alert">
        {{ chartsStore.error }}
      </div>

      <PlotlyViewer
        v-else-if="chartsStore.chart"
        :chart="chartsStore.chart"
        :isLoading="chartsStore.isLoading"
        :error="chartsStore.error"
        aria-label="Gráfico de séries de ratios da empresa selecionada"
      />

      <div v-else class="muted">
        Selecione uma companhia na Home. Os gráficos das 4 contas principais serão carregados automaticamente.
      </div>
    </main>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'

import PlotlyViewer from '../components/PlotlyViewer.vue'
import { useAccountChartsStore } from '../store/accountChartsStore'
import { useCompanyStore } from '../store/companyStore'

const chartsStore = useAccountChartsStore()
const companyStore = useCompanyStore()
const route = useRoute()

const { selectedPairs, filterQuery } = storeToRefs(companyStore)

const activeCompanyName = computed(() => {
  const fromRoute = route.query.company
  if (typeof fromRoute === 'string' && fromRoute.trim().length > 0) {
    return fromRoute.trim()
  }

  const pairs = selectedPairs.value || []
  if (!pairs.length) {
    return ''
  }
  return pairs[0].company || ''
})

// 4 contas padrão
const localAccounts = ref(['02.03', '03.01', '04.02', '05.01'])

watch(
  activeCompanyName,
  (name) => {
    chartsStore.setCompanyName(name)
    chartsStore.resetChart()
  },
  { immediate: true },
)

watch(
  filterQuery,
  (query) => {
    chartsStore.setFilterFromFilterQuery(query)
  },
  { deep: true, immediate: true },
)

watch(
  localAccounts,
  (accounts) => {
    chartsStore.setSelectedAccounts(accounts)
    chartsStore.resetChart()
  },
  { deep: true, immediate: true },
)

watch(
  [activeCompanyName, localAccounts, filterQuery],
  async ([name, accounts]) => {
    if (!name || !accounts.length || chartsStore.isLoading) {
      return
    }

    await chartsStore.loadChart()
  },
  { deep: true, immediate: true },
)
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

.muted {
  color: #64748b;
  font-size: 0.95rem;
}
</style>

