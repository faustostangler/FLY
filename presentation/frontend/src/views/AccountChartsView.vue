<template>
  <section class="account-charts">
    <header class="account-charts__header">
      <h2>Gráficos por conta contábil</h2>
      <p>
        Informe um ticker e visualize múltiplas contas financeiras usando o mesmo
        pipeline.
      </p>
    </header>

    <div class="account-charts__controls">
      <label for="ticker-input">Ticker</label>
      <input
        id="ticker-input"
        v-model="localTicker"
        type="text"
        placeholder="Ex.: PETR4"
        @keyup.enter="load"
      />

      <button type="button" @click="load">
        Carregar gráficos
      </button>
    </div>

    <div class="account-charts__grid">
      <section class="account-chart" aria-live="polite">
        <h3>02.03 – Patrimônio Líquido</h3>
        <PlotlyViewer
          :chart="charts['02.03']"
          :isLoading="isLoading['02.03']"
          :error="error['02.03']"
        />
      </section>

      <section class="account-chart" aria-live="polite">
        <h3>03.01 – Receita Líquida</h3>
        <PlotlyViewer
          :chart="charts['03.01']"
          :isLoading="isLoading['03.01']"
          :error="error['03.01']"
        />
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useAccountChartsStore } from '../store/accountChartsStore'
import PlotlyViewer from '../components/PlotlyViewer.vue'

const store = useAccountChartsStore()
const localTicker = ref(store.ticker)

const charts = computed(() => store.charts)
const isLoading = computed(() => store.isLoading)
const error = computed(() => store.error)

async function load() {
  store.setTicker(localTicker.value)
  await store.loadMultipleAccounts(['02.03', '03.01'])
}
</script>

<style scoped>
.account-charts {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem;
}

.account-charts__header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.account-charts__controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.account-charts__controls input {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  min-width: 160px;
}

.account-charts__controls button {
  padding: 0.5rem 1rem;
  border: none;
  background-color: #2563eb;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
}

.account-charts__controls button:hover {
  background-color: #1d4ed8;
}

.account-charts__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.account-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
</style>
