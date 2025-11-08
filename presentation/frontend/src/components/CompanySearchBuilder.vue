<template>
  <section class="company-search">
    <header class="company-search__header">
      <h2>Construtor de filtros</h2>
      <div class="company-search__actions">
        <button type="button" class="ghost" @click="clearFilters">Limpar filtros</button>
        <button type="button" @click="reload">Buscar</button>
      </div>
    </header>

    <section class="company-search__facets" aria-labelledby="filters-heading">
      <h2 id="filters-heading">Filtros</h2>

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
    </section>

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
        <span v-if="parseError" class="company-search__error">
          {{ parseError }}
        </span>
      </div>
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
            <button
              type="button"
              class="tag"
              :class="{ 'tag--active': isActiveTicker(item.ticker) }"
              @click="selectTicker(item.ticker)"
            >
              {{ item.ticker }}
            </button>
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
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCompanyStore } from '../store/companyStore'
import { useChartStore } from '../store/chartStore'
import CompanyFacet from './CompanyFacet.vue'
import CompanyResultSelect from './CompanyResultSelect.vue'

const store = useCompanyStore()
const chartStore = useChartStore()
const route = useRoute()
const router = useRouter()

const facetConfigs = computed(() => store.facetConfigs || [])
const companies = computed(() => store.companies || [])
const total = computed(() => store.total ?? companies.value.length)
const error = computed(() => store.error)
const isLoading = computed(() => store.isLoading)
const parseError = computed(() => store.parseError)
const selectedTicker = computed(() => store.selectedTicker)

const queryTextModel = computed({
  get: () => store.queryText,
  set: (value) => store.updateQueryText(value),
})

const selectedItemsModel = computed({
  get: () => store.selectedItems,
  set: (value) => store.updateSelectedItems(value),
})

const selectedSummaries = computed(() => store.selectedSummaries || [])

const facetOptions = (field) => store.facetOptions(field)
const clauseValues = (field) => store.clauseValues(field)
const clauseLogical = (field) => store.clauseLogical(field)

const reload = () => store.reload()
const clearFilters = () => store.clearFilters()
const applyQuery = () => store.applyQuery()

const onFacetChange = (payload) => {
  store.updateFacet(payload)
}

function selectTicker(ticker) {
  if (!ticker) {
    return
  }
  const value = String(ticker)
  if (store.selectedTicker !== value) {
    store.setSelectedTicker(value)
  }
  chartStore.loadChartByTicker(value)

  const currentType = typeof route.query.type === 'string' ? route.query.type : undefined
  if (currentType !== value) {
    router.replace({ query: { ...route.query, type: value } })
  }
}

function isActiveTicker(ticker) {
  return selectedTicker.value === ticker
}

onMounted(() => {
  if (!store.companies.length) {
    store.loadCompanies()
  }
})
</script>

<style scoped>
.company-search {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.company-search__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.company-search__actions {
  display: flex;
  gap: 0.5rem;
}

.company-search__facets {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.company-search__query {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.company-search__query textarea {
  width: 100%;
  resize: vertical;
}

.company-search__query-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.company-search__results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.company-search__error {
  color: #d93025;
}

.company-search__status {
  color: #2563eb;
}

.company-search__selection {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 0;
  padding: 0;
  list-style: none;
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
  display: inline-flex;
  align-items: center;
  background: #0f172a;
  color: #fff;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  font-size: 0.8rem;
  gap: 0.25rem;
  border: none;
  cursor: pointer;
}

.tag:focus-visible {
  outline: 2px solid #1d4ed8;
  outline-offset: 2px;
}

.tag--outline {
  background: transparent;
  color: #0f172a;
  border: 1px solid #0f172a;
  cursor: default;
}

.tag--active {
  background: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

.muted {
  color: #666;
}

button {
  padding: 0.5rem 1rem;
}

button.ghost {
  background: transparent;
  border: 1px solid currentColor;
}
</style>
