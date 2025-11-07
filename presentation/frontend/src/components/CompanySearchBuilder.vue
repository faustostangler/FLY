<template>
  <section class="company-search">
    <header class="company-search__header">
      <h2>Construtor de filtros</h2>
      <div class="company-search__actions">
        <button type="button" class="ghost" @click="clearFilters">
          Limpar filtros
        </button>
        <button type="button" @click="reload">Buscar</button>
      </div>
    </header>

    <div class="company-search__query">
      <label for="queryText">Consulta estruturada</label>
      <textarea
        id="queryText"
        v-model="queryTextModel"
        rows="2"
        placeholder="AND sector IN (Energia, Financeiro)"
      ></textarea>
      <div class="company-search__query-actions">
        <button type="button" @click="applyQuery">Aplicar consulta</button>
        <span v-if="parseError" class="company-search__error">{{ parseError }}</span>
      </div>
    </div>

    <div class="company-search__facets">
      <CompanyFacet
        v-for="facet in facetConfigs"
        :key="facet.field"
        :field="facet.field"
        :label="facet.label"
        :options="facetOptions(facet.field)"
        :logical="clauseLogical(facet.field)"
        :values="clauseValues(facet.field)"
        :multiple="facet.multiple !== false"
        @change="onFacetChange"
      />
    </div>

    <div class="company-search__results">
      <header>
        <h3>Resultados ({{ total }})</h3>
        <span v-if="isLoading" class="company-search__status">Carregando...</span>
        <span v-else-if="error" class="company-search__error">{{ error }}</span>
      </header>

      <CompanyResultSelect
        v-model="selectedItemsModel"
        :companies="companies"
        :disabled="isLoading || !companies.length"
      />

      <p v-if="!companies.length && !isLoading" class="muted">
        Nenhuma companhia encontrada com os filtros atuais.
      </p>
      <p v-else-if="!selectedSummaries.length" class="muted">
        Use o menu para escolher uma ou mais combinações de companhia e ticker.
      </p>
      <ul v-else class="company-search__selection">
        <li v-for="item in selectedSummaries" :key="item.key">
          <h4>{{ item.companyName }}</h4>
          <div class="company-search__tags">
            <span class="tag">{{ item.ticker }}</span>
            <span v-if="item.market" class="tag tag--outline">{{ item.market }}</span>
          </div>
          <p v-if="item.tradingName" class="muted">{{ item.tradingName }}</p>
          <p class="muted">
            <span v-if="item.sector">Setor: {{ item.sector }} · </span>
            <span v-if="item.subsector">Subsetor: {{ item.subsector }} · </span>
            <span v-if="item.segment">Segmento: {{ item.segment }}</span>
          </p>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { COMPANY_FACETS } from '../config/companyFacets'
import { useCompanyStore } from '../store/companyStore'
import CompanyFacet from './CompanyFacet.vue'
import CompanyResultSelect from './CompanyResultSelect.vue'

const store = useCompanyStore()

const facetConfigs = COMPANY_FACETS
const parseError = ref('')

const queryTextModel = computed({
  get: () => store.queryText,
  set: (value) => {
    parseError.value = ''
    store.setQueryText(value)
  },
})

const companies = computed(() => store.companies)
const total = computed(() => store.total)
const facets = computed(() => store.facets || {})
const isLoading = computed(() => store.isLoading)
const error = computed(() => store.error)

const selectedItemsModel = computed({
  get: () => store.selectedItems,
  set: (values) => store.setSelectedItems(values),
})

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

function facetOptions(field) {
  return facets.value[field] || []
}

function clauseLogical(field) {
  return store.clauseByField[field]?.logical || 'AND'
}

function clauseValues(field) {
  return store.clauseByField[field]?.condition?.values || []
}

function onFacetChange({ field, logical, values }) {
  store.setFacetSelection(field, logical, values)
}

function applyQuery() {
  const result = store.applyQueryText()
  if (!result.ok) {
    parseError.value = result.message || 'Não foi possível interpretar a consulta.'
    return
  }
  parseError.value = ''
}

function clearFilters() {
  store.resetFilters()
  parseError.value = ''
}

function reload() {
  store.loadCompanies()
}

onMounted(() => {
  if (!store.companies.length) {
    reload()
  }
})
</script>

<style scoped>
.company-search {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem;
  border: 1px solid var(--vt-c-divider-light, #e2e8f0);
  border-radius: 12px;
  background-color: var(--vt-c-bg-mute, #f8fafc);
}

.company-search__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.company-search__actions {
  display: flex;
  gap: 0.5rem;
}

.company-search__actions button {
  padding: 0.35rem 0.9rem;
  border-radius: 6px;
  border: none;
  background: #0f172a;
  color: #fff;
  cursor: pointer;
}

.company-search__actions .ghost {
  background: transparent;
  border: 1px solid #0f172a;
  color: #0f172a;
}

.company-search__query label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.company-search__query textarea {
  width: 100%;
  border-radius: 8px;
  border: 1px solid #cbd5f5;
  padding: 0.5rem;
  font-family: 'JetBrains Mono', monospace;
  resize: vertical;
}

.company-search__query-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.company-search__query-actions button {
  padding: 0.35rem 0.9rem;
  border-radius: 6px;
  border: none;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}

.company-search__facets {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.company-search__results header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

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

.company-search__status {
  color: #2563eb;
  font-size: 0.9rem;
}

.company-search__error {
  color: #dc2626;
  font-size: 0.9rem;
}
</style>
