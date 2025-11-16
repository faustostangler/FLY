<template>
  <section class="company-search">
    <header class="company-search__header">
      <h2>Construtor de filtros</h2>
      <div class="company-search__actions">
        <button type="button" @click="reload">Consultar</button>
        <button type="button" class="ghost" @click="clearFilters">Limpar filtros</button>
      </div>
    </header>

    <section class="company-search__facets" aria-labelledby="filters-heading">
      <h2 id="filters-heading">Filtros</h2>

      <CompanyFacet
        v-for="facet in facets"
        :key="facet.key"
        :facet-key="facet.key"
        :label="facet.label"
        :options="facetOptionsByKey[facet.key] || []"
        :model-value="facetSelectionByKey[facet.key] || []"
        :multiple="facet.multiple !== false"
        :type="facet.type || 'text'"
        :searchable="Boolean(facet.searchable)"
        @update:modelValue="(values) => companyStore.setFacetSelection(facet.key, values)"
      />
    </section>

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
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { COMPANY_FACETS } from '../config/companyFacets'
import { useCompanyStore } from '../store/companyStore'
import { useChartStore } from '../store/chartStore'
import { extractTickers } from '../utils/tickers'
import CompanyFacet from './CompanyFacet.vue'
import CompanyResultSelect from './CompanyResultSelect.vue'

const companyStore = useCompanyStore()
const chartStore = useChartStore()
const route = useRoute()
const router = useRouter()
let isSyncingSelection = false

const facets = COMPANY_FACETS

const facetOptionsByKey = computed(() => companyStore.facetOptions || {})
const facetSelectionByKey = computed(() => companyStore.activeFacetFilters || {})

const companies = computed(() => companyStore.filteredCompanies || [])
const total = computed(() => companyStore.total)
const isLoading = computed(() => companyStore.isLoading)
const error = computed(() => companyStore.error)

const selectedItemsModel = computed({
  get: () => companyStore.selectedItems,
  set: (values) => {
    onSelectionChange(values)
  },
})

function normalizeSelection(values) {
  if (!Array.isArray(values)) {
    return []
  }
  return values
    .map((value) => String(value || '').trim())
    .filter((value) => value.length)
}

function parseSelectionParam(rawValue) {
  if (!rawValue) {
    return []
  }

  const values = Array.isArray(rawValue) ? rawValue : [rawValue]

  return values
    .flatMap((entry) => String(entry || '').split(','))
    .map((entry) => entry.trim())
    .filter((entry) => entry.length)
}

function selectionsAreEqual(a = [], b = []) {
  if (a.length !== b.length) {
    return false
  }
  return a.every((value, index) => value === b[index])
}

async function syncChartWithSelection(selectionValues, { forceLoad = false } = {}) {
  const tickers = extractTickers(selectionValues)
  const [primaryTicker, ...comparisonTickers] = tickers
  const currentType = chartStore.params.type || ''
  const currentSelection = chartStore.params.selection || []

  const typeChanged = primaryTicker !== currentType
  const selectionChanged = !selectionsAreEqual(comparisonTickers, currentSelection)

  if (typeChanged) {
    chartStore.setType(primaryTicker)
  }
  if (selectionChanged) {
    chartStore.setSelection(comparisonTickers)
  }

  if (forceLoad || typeChanged || selectionChanged) {
    await chartStore.loadChart()
  }
}

async function onSelectionChange(values) {
  if (isSyncingSelection) {
    return
  }

  isSyncingSelection = true

  try {
    const normalized = normalizeSelection(values)
    const current = companyStore.selectedItems || []
    const querySelection = parseSelectionParam(route.query.selection)
    const selectionChanged = !selectionsAreEqual(normalized, current)

    if (selectionChanged) {
      companyStore.setSelectedItems(normalized)
    }

    const selectionParam = normalized.join(',')
    const nextQuery = {
      ...route.query,
      selection: selectionParam || undefined,
    }

    if (!selectionsAreEqual(normalized, querySelection)) {
      try {
        await router.replace({ query: nextQuery })
      } catch (error) {
        console.error(error)
      }
    }

    await syncChartWithSelection(normalized, { forceLoad: selectionChanged })
  } finally {
    isSyncingSelection = false
  }
}

function clearFilters() {
  companyStore.clearAllFacets()
  companyStore.setSelectedItems([])
}

function reload() {
  companyStore.loadCompanies()
}

onMounted(async () => {
  if (!companyStore.allCompanies.length) {
    await companyStore.loadCompanies()
  }

  const initialSelection = parseSelectionParam(route.query.selection)

  isSyncingSelection = true
  try {
    const current = companyStore.selectedItems || []
    if (!selectionsAreEqual(initialSelection, current)) {
      companyStore.setSelectedItems(initialSelection)
    }
  } finally {
    isSyncingSelection = false
  }

  const normalizedSelection = companyStore.selectedItems || initialSelection
  await syncChartWithSelection(normalizedSelection, { forceLoad: true })
})

watch(
  () => companyStore.selectedItems,
  async (values) => {
    if (isSyncingSelection) {
      return
    }

    const normalized = normalizeSelection(values)
    const querySelection = parseSelectionParam(route.query.selection)

    const needsQuerySync = !selectionsAreEqual(normalized, querySelection)

    if (needsQuerySync) {
      await onSelectionChange(normalized)
      return
    }

    await syncChartWithSelection(normalized)
  },
  { deep: true },
)

watch(
  () => route.query.selection,
  async (value) => {
    if (isSyncingSelection) {
      return
    }

    isSyncingSelection = true
    try {
      const parsed = parseSelectionParam(value)
      const companySelection = companyStore.selectedItems || []

      if (!selectionsAreEqual(parsed, companySelection)) {
        companyStore.setSelectedItems(parsed)
      }

      await syncChartWithSelection(parsed)
    } finally {
      isSyncingSelection = false
    }
  },
)
</script>

<style scoped>
.company-search {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem;
  border: 1px solid var(--vt-c-divider-light, #e2e8f0);
  border-radius: 12px;
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

.company-search__actions button:not(.ghost) {
  background: #2563eb;
}

.company-search__facets {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.company-search__facets > h2 {
  grid-column: 1 / -1;
  margin: 0;
}

.company-search__results header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
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
