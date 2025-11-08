<template>
  <section aria-labelledby="company-heading">
    <h3 id="company-heading">Companhia</h3>

    <p v-if="!selectedSummaries.length" class="muted">
      Use o menu de resultados para escolher uma ou mais combinações de companhia e ticker.
    </p>

    <ul v-else class="company-search__selection">
      <li v-for="item in selectedSummaries" :key="item.key">
        <h4>{{ item.companyName }}</h4>

        <div class="company-search__tags">
          <span class="tag">{{ item.ticker }}</span>
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
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useCompanyStore } from '../store/companyStore'

const store = useCompanyStore()

const selectedSummaries = computed(() => {
  const index = new Map()

  for (const company of store.companies || []) {
    const companyName = company.company_name || ''

    for (const ticker of company.tickers || []) {
      if (!ticker) continue

      const key = `${companyName}::${ticker}`

      index.set(key, {
        key,
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

  return (store.selectedItems || [])
    .map((value) => index.get(value))
    .filter(Boolean)
})
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

.muted {
  color: #64748b;
  margin: 0.1rem 0 0;
}
</style>
