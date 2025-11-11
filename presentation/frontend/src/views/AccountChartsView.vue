<template>
  <section class="account-charts">
    <header class="account-charts__header">
      <h2>Gráficos de ratios por empresa</h2>

      <p v-if="activeCompanyName">
        Companhia selecionada:
        <strong>{{ activeCompanyName }}</strong>
      </p>
      <p v-else class="muted">
        Nenhuma companhia selecionada. Utilize os filtros na busca para escolher uma.
      </p>

      <div class="account-charts__controls">
        <label class="account-charts__select">
          Contas
          <select multiple v-model="localAccounts">
            <option value="02.03">02.03 – Patrimônio Líquido</option>
            <option value="03.01">03.01 – Receita Líquida</option>
            <option value="04.02">04.02 – EBITDA</option>
            <option value="05.01">05.01 – Lucro Líquido</option>
          </select>
        </label>

        <button
          type="button"
          class="account-charts__button"
          @click="onReload"
          :disabled="!canReload"
        >
          Carregar gráficos
        </button>
      </div>
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
        Selecione uma companhia, escolha as contas desejadas e clique em “Carregar gráficos”.
      </div>
    </main>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'

import PlotlyViewer from '../components/PlotlyViewer.vue'
import { useAccountChartsStore } from '../store/accountChartsStore'
import { useCompanyStore } from '../store/companyStore'

const chartsStore = useAccountChartsStore()
const companyStore = useCompanyStore()

const { selectedPairs, filterQuery } = storeToRefs(companyStore)

const activeCompanyName = computed(() => {
  const pairs = selectedPairs.value || []
  if (!pairs.length) {
    return ''
  }
  return pairs[0].company || ''
})

const localAccounts = ref(['02.03', '03.01'])

const canReload = computed(() => {
  return Boolean(activeCompanyName.value && localAccounts.value.length && !chartsStore.isLoading)
})

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

async function onReload() {
  await chartsStore.loadChart()
}
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

.account-charts__controls {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
}

.account-charts__select {
  display: grid;
  gap: 0.5rem;
  font-weight: 600;
}

.account-charts__select select {
  min-width: 220px;
  min-height: 96px;
  padding: 0.5rem;
  border: 1px solid #cbd5f5;
  border-radius: 4px;
}

.account-charts__button {
  padding: 0.5rem 1.25rem;
  border: none;
  border-radius: 4px;
  background-color: #2563eb;
  color: #fff;
  cursor: pointer;
}

.account-charts__button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.account-charts__body {
  min-height: 280px;
}

.muted {
  color: #64748b;
  font-size: 0.95rem;
}
</style>

