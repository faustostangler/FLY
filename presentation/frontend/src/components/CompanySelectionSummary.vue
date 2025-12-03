<template>
  <section aria-labelledby="company-heading">
    <h3 id="company-heading">Companhia</h3>

    <p v-if="!selectedSummaries.length" class="muted">
      Use o menu de resultados para escolher uma ou mais combinações de companhia e ticker.
    </p>

    <ul v-else class="company-search__selection">
      <li v-for="item in selectedSummaries" :key="item.value">
        <h4>{{ item.companyName }}</h4>

        <div class="company-search__tags">
          <button
            type="button"
            class="tag tag--clickable"
            @click="onTickerClick(item)"
          >
            {{ item.ticker }}
          </button>
          <span v-if="item.market" class="tag tag--outline">{{ item.market }}</span>
        </div>

        <p v-if="item.tradingName" class="muted">
          {{ item.tradingName }}
        </p>

        <p class="muted">
          <span v-if="item.sector">Setor: {{ item.sector }} · </span>
          <span v-if="item.subsector">Subsetor: {{ item.subsector }} · </span>
          <span v-if="item.segment">Segmento: {{ item.segment }}</span>
        </p>
      </li>
    </ul>

    <div class="home__selected-actions-bar">
      <button
        type="button"
        class="home__charts-button"
        :disabled="!hasSelection"
        @click="emitVisualizarGraficos"
      >
        Visualizar Gráficos
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useCompanyStore } from '../store/companyStore'
import { useChartStore } from '../store/chartStore'
import { extractTicker } from '../utils/tickers'

const props = defineProps({
  selectedPairs: {
    type: Array,
    required: false,
    default: () => [],
  },
})

const emit = defineEmits(['visualizar-graficos'])

const companyStore = useCompanyStore()
const chartStore = useChartStore()

const selectedSummaries = computed(() => {
  const index = new Map()

  for (const company of companyStore.filteredCompanies || []) {
    const companyName = company.company_name || ''

    for (const ticker of company.tickers || []) {
      if (!ticker) continue

      const value = `${companyName}::${ticker}`

      if (!index.has(value)) {
        index.set(value, {
          value,
          companyName,
          ticker,
          tradingName: company.trading_name || '',
          sector: company.sector || '',
          subsector: company.subsector || '',
          segment: company.segment || '',
          market: company.market || '',
        })
      }
    }
  }

  return (companyStore.selectedItems || [])
    .map((value) => index.get(value))
    .filter(Boolean)
})

const hasSelection = computed(() => {
  if (props.selectedPairs && props.selectedPairs.length > 0) {
    return true
  }

  return selectedSummaries.value.length > 0
})

const emitVisualizarGraficos = () => {
  if (!hasSelection.value) return
  emit('visualizar-graficos')
}

async function onTickerClick(item) {
  if (!item?.value) {
    return
  }

  const selection = [item.value]
  const ticker = extractTicker(item.value)

  companyStore.setSelectedItems(selection)
  chartStore.setType(ticker)
  chartStore.setSelection([])
  await chartStore.loadChart()
}
</script>

<style scoped>
.company-search__selection {
  list-style: none;
  padding: 0;
  margin: 1rem 0 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.company-search__selection li {
  padding: 0.75rem;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
}

.company-search__selection h4 {
  margin: 0;
  font-size: 1.1rem;
}

.company-search__tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 0.5rem 0;
}

.tag {
  background: #0f172a;
  color: #fff;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.8rem;
}

.tag--outline {
  background: transparent;
  color: #0f172a;
  border: 1px solid #0f172a;
}

.tag--clickable {
  cursor: pointer;
  border: none;
}

.tag--clickable:focus-visible {
  outline: 2px solid #1d4ed8;
  outline-offset: 2px;
}

.muted {
  color: #64748b;
  margin: 0.1rem 0 0;
}

.home__selected-actions-bar {
  margin-top: 1rem;
  display: flex;
  justify-content: flex-end;
}

.home__charts-button {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s ease;
}

.home__charts-button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.home__charts-button:not(:disabled):hover {
  background: #1d4ed8;
}
</style>
