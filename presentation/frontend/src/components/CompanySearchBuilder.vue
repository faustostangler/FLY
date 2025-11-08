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

    <section class="company-search__facets" aria-labelledby="filters-heading">
      <h2 id="filters-heading">Filtros</h2>

      <CompanyFacet
        v-for="facet in facetConfigs"
        :key="facet.field"
        :field="facet.field"
        :label="facet.label"
        :options="facetOptions(facet.field)"
        :logical="facetLogical(facet.field)"
        :values="facetValues(facet.field)"
        :multiple="facet.multiple !== false"
        @change="onFacetDraftChange"
        @commit="onFacetCommit"
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
        <span v-if="parseError" class="company-search__error">{{ parseError }}</span>
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
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { COMPANY_FACETS } from '../config/companyFacets'
import { useCompanyStore } from '../store/companyStore'
import { useChartStore } from '../store/chartStore'
import CompanyFacet from './CompanyFacet.vue'
import CompanyResultSelect from './CompanyResultSelect.vue'

const store = useCompanyStore()
const chartStore = useChartStore()
const route = useRoute()
const router = useRouter()
let isSyncingSelection = false

const facetConfigs = COMPANY_FACETS
const parseError = ref('')
const draftFacets = ref({})

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

function facetOptions(field) {
  return facets.value[field] || []
}

function facetLogical(field) {
  const draft = draftFacets.value[field]
  if (draft && draft.logical) {
    return draft.logical
  }
  return store.clauseByField[field]?.logical || 'AND'
}

function facetValues(field) {
  const draft = draftFacets.value[field]
  if (draft && Array.isArray(draft.values)) {
    return draft.values
  }
  return store.clauseByField[field]?.condition?.values || []
}

function onFacetDraftChange({ field, logical, values }) {
  draftFacets.value = {
    ...draftFacets.value,
    [field]: {
      logical: logical || 'AND',
      values: Array.isArray(values) ? [...values] : [],
    },
  }
}

function onFacetCommit({ field, logical, values }) {
  const finalLogical = logical || 'AND'
  const finalValues = Array.isArray(values) ? [...values] : []

  store.setFacetSelection(field, finalLogical, finalValues)

  draftFacets.value = {
    ...draftFacets.value,
    [field]: {
      logical: finalLogical,
      values: [],
    },
  }
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
  draftFacets.value = {}
}

function reload() {
  store.loadCompanies()
}

async function onSelectionChange(values) {
  if (isSyncingSelection) {
    return
  }

  isSyncingSelection = true

  try {
    const normalized = normalizeSelection(values)
    const current = store.selectedItems || []
    const querySelection = parseSelectionParam(route.query.selection)

    if (!selectionsAreEqual(normalized, current)) {
      store.setSelectedItems(normalized)
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

    chartStore.setSelection(normalized)
    await chartStore.loadChart()
  } finally {
    isSyncingSelection = false
  }
}

onMounted(async () => {
  const initialSelection = parseSelectionParam(route.query.selection)
  const current = store.selectedItems || []
  const chartSelection = chartStore.params.selection || []

  if (!selectionsAreEqual(initialSelection, current)) {
    store.setSelectedItems(initialSelection)
  }

  const selectionChanged = !selectionsAreEqual(initialSelection, chartSelection)
  if (selectionChanged) {
    chartStore.setSelection(initialSelection)
    await chartStore.loadChart()
  }
})

watch(
  () => store.selectedItems,
  (values) => {
    if (isSyncingSelection) {
      return
    }

    const normalized = normalizeSelection(values)
    const querySelection = parseSelectionParam(route.query.selection)
    const chartSelection = chartStore.params.selection || []

    const needsQuerySync = !selectionsAreEqual(normalized, querySelection)
    const needsChartSync = !selectionsAreEqual(normalized, chartSelection)

    if (needsQuerySync || needsChartSync) {
      onSelectionChange(normalized)
    }
  },
  { deep: true },
)

watch(
  () => route.query.selection,
  async (value) => {
    if (isSyncingSelection) {
      return
    }

    const parsed = parseSelectionParam(value)
    const companySelection = store.selectedItems || []
    const chartSelection = chartStore.params.selection || []

    if (!selectionsAreEqual(parsed, companySelection)) {
      store.setSelectedItems(parsed)
    }

    if (!selectionsAreEqual(parsed, chartSelection)) {
      chartStore.setSelection(parsed)
      await chartStore.loadChart()
    }
  },
)

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

.company-search__actions button:not(.ghost) {
  background: #2563eb;
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
