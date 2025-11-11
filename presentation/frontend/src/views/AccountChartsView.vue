<template>
  <section class="account-charts">
    <header class="account-charts__header">
      <h2>Gráficos de ratios por empresa</h2>
      <p v-if="activeCompanyName">
        Companhia selecionada: <strong>{{ activeCompanyName }}</strong>
      </p>
      <p v-else class="muted">
        Nenhuma companhia selecionada. Use o construtor de filtros para escolher uma.
      </p>

      <div class="account-charts__controls">
        <label>
          Contas
          <select multiple v-model="localAccounts">
            <option value="02.03">02.03 – Patrimônio Líquido</option>
            <option value="03.01">03.01 – Receita Líquida</option>
            <option value="04.02">04.02 – EBITDA</option>
          </select>
        </label>

        <button
          type="button"
          @click="onReload"
          :disabled="!canReload || chartsStore.isLoading"
        >
          Carregar gráficos
        </button>
      </div>
    </header>

    <main class="account-charts__body" aria-live="polite">
      <div v-if="cacheStatus" class="account-charts__cache">
        <span :class="['badge', cacheStatus === 'hit' ? 'badge--hit' : 'badge--miss']">
          Cache {{ cacheStatus === 'hit' ? 'hit' : 'miss' }}
        </span>
      </div>

      <div v-if="chartsStore.isLoading" class="status">Carregando séries de ratios...</div>
      <div v-else-if="chartsStore.error" class="status status--error">{{ chartsStore.error }}</div>
      <PlotlyViewer
        v-else-if="chartsStore.chart"
        :chart="chartsStore.chart"
        :loading="chartsStore.isLoading"
        :error="chartsStore.error"
      />
      <div v-else class="status">Selecione contas e carregue o gráfico.</div>
    </main>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { debounce } from 'lodash-es'
import PlotlyViewer from '../components/PlotlyViewer.vue'
import { useAccountChartsStore } from '../store/accountChartsStore'
import { useCompanyStore } from '../store/companyStore'

const chartsStore = useAccountChartsStore()
const companyStore = useCompanyStore()

const { selectedPairs, filterQuery } = storeToRefs(companyStore)

const activeCompanyName = computed(() => {
  const pair = (selectedPairs.value || [])[0]
  return pair?.company || ''
})

const localAccounts = ref(['02.03', '03.01'])

const canReload = computed(() => {
  return Boolean(activeCompanyName.value && localAccounts.value.length && !chartsStore.isLoading)
})

const cacheStatus = computed(() => {
  const meta = chartsStore.chart?.meta
  if (!meta || !meta.cache || typeof meta.cache.hit !== 'boolean') {
    return null
  }
  return meta.cache.hit ? 'hit' : 'miss'
})

const autoReloadReady = ref(false)
const debouncedReload = debounce(() => {
  if (canReload.value) {
    chartsStore.loadChart()
  }
}, 500)

watch(
  activeCompanyName,
  (name) => {
    chartsStore.setCompanyName(name)
    chartsStore.resetChart()
    if (autoReloadReady.value && name) {
      debouncedReload()
    }
  },
  { immediate: true },
)

watch(
  filterQuery,
  (query) => {
    chartsStore.setFilterFromFilterQuery(query)
    chartsStore.resetChart()
    if (autoReloadReady.value) {
      debouncedReload()
    }
  },
  { immediate: true, deep: true },
)

watch(
  localAccounts,
  (accounts) => {
    chartsStore.setSelectedAccounts(accounts)
    chartsStore.resetChart()
    if (autoReloadReady.value) {
      debouncedReload()
    }
  },
  { immediate: true, deep: true },
)

async function onReload() {
  await chartsStore.loadChart()
}

onMounted(() => {
  autoReloadReady.value = true
})

onBeforeUnmount(() => {
  debouncedReload.cancel()
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
  gap: 1rem;
}

.account-charts__controls {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
}

.account-charts__controls select {
  min-width: 220px;
  min-height: 6rem;
}

.account-charts__controls button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  background-color: #2563eb;
  color: #fff;
  cursor: pointer;
}

.account-charts__controls button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.account-charts__body {
  min-height: 320px;
  display: grid;
  gap: 0.75rem;
}

.account-charts__cache {
  display: flex;
  justify-content: flex-end;
}

.status {
  padding: 1rem;
  border: 1px dashed #cbd5f5;
  border-radius: 8px;
  color: #1e3a8a;
}

.status--error {
  border-color: #f87171;
  color: #b91c1c;
}

.muted {
  color: #6b7280;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge--hit {
  background-color: #e6f4ea;
  color: #1e7a36;
}

.badge--miss {
  background-color: #fdecea;
  color: #b23b28;
}
</style>
