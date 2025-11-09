<template>
  <section class="company-search">
    <header class="company-search__header">
      <h2>Construtor de filtros</h2>
    </header>

    <section class="company-search__facets" aria-labelledby="filters-heading">
      <h2 id="filters-heading">Filtros</h2>

      <CompanyFacet
        v-for="facet in facetConfigs"
        :key="facet.field"
        :field="facet.field"
        :label="facet.label"
        :options="facetOptions(facet)"
        :logical="facetLogical(facet.field)"
        :operator="facetOperator(facet)"
        :values="structuredFilters[facet.field] || []"
        :multiple="facet.multiple !== false"
        :type="facet.type || 'text'"
        :searchable="Boolean(facet.searchable)"
        :model-value="facetModelValue(facet.field)"
        @update:modelValue="(values) => onFacetSelectionChange(facet.field, values)"
        @commit="onFacetCommit"
      />
    </section>

    <div class="company-search__query">
      <label for="queryText">Consulta estruturada</label>
      <textarea
        id="queryText"
        :value="queryText"
        rows="3"
        readonly
        placeholder="Nenhum filtro estruturado definido"
      ></textarea>
      <div class="company-search__actions">
        <button type="button" @click="onEnviarParaConsulta">
          Enviar seleção das facetas para consulta
        </button>
        <button type="button" @click="onPesquisar">Pesquisar</button>
        <button type="button" class="ghost" @click="clearFilters">
          Limpar filtros
        </button>
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
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { COMPANY_FACETS } from '../config/companyFacets'
import { useCompanyStore } from '../store/companyStore'
import { useChartStore } from '../store/chartStore'
import { extractTickers } from '../utils/tickers'
import CompanyFacet from './CompanyFacet.vue'
import CompanyResultSelect from './CompanyResultSelect.vue'

const store = useCompanyStore()
const chartStore = useChartStore()
const route = useRoute()
const router = useRouter()
let isSyncingSelection = false

const facetConfigs = COMPANY_FACETS

const companies = computed(() => store.companies)
const total = computed(() => store.total)
const facets = computed(() => store.facets || {})
const cascadeFilters = computed(() => store.cascadeFilters || {})
const structuredFilters = computed(() => store.structuredFilters || {})
const queryText = computed(() => store.queryText || '')
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

function booleanLabel(value) {
  if (value === 'true') return 'Sim'
  if (value === 'false') return 'Não'
  return value
}

function facetOptions(facet) {
  const field = facet.field
  const dynamic = facets.value[field] || []

  if (facet.type === 'boolean') {
    const base = Array.isArray(facet.options) ? facet.options : []
    const normalized = []
    const seen = new Set()

    const pushOption = (rawValue, rawLabel) => {
      if (rawValue === null || rawValue === undefined || rawValue === '') {
        return
      }
      const stringValue = String(rawValue).toLowerCase()
      if (!stringValue) return
      if (seen.has(stringValue)) return
      seen.add(stringValue)
      const label = rawLabel ?? booleanLabel(stringValue)
      normalized.push({ value: stringValue, label })
    }

    for (const option of base) {
      if (option && typeof option === 'object') {
        pushOption(option.value ?? option.label ?? '', option.label)
      } else {
        pushOption(option, undefined)
      }
    }

    for (const option of dynamic) {
      if (option && typeof option === 'object') {
        pushOption(option.value ?? option.label ?? '', option.label)
      } else if (typeof option === 'boolean') {
        pushOption(option ? 'true' : 'false', undefined)
      } else {
        pushOption(option, undefined)
      }
    }

    return normalized
  }

  if (facet.type === 'date-range') {
    return facet.options || []
  }

  if (dynamic.length) {
    return dynamic
  }

  return facet.options || []
}

const CASCADE_FIELDS = ['industry_sector', 'industry_subsector', 'industry_segment']

function isCascadeField(field) {
  return CASCADE_FIELDS.includes(field)
}

function facetModelValue(field) {
  if (isCascadeField(field)) {
    return cascadeFilters.value[field] || []
  }
  return structuredFilters.value[field] || []
}

function facetLogical(field) {
  return 'AND'
}

function facetOperator(facet) {
  if (!facet) return 'IN'
  if (facet.type === 'date-range') {
    return 'BETWEEN'
  }
  if (facet.type === 'boolean') {
    return 'EQUALS'
  }
  return facet.multiple === false ? 'EQUALS' : 'IN'
}

function onFacetSelectionChange(field, values) {
  if (isCascadeField(field)) {
    store.setCascadeFacetSelection(field, values)
    return
  }

  store.setStructuredFilter(field, values)
}

function onFacetCommit(payload = {}) {
  const { field, values } = payload
  if (!field) {
    return
  }
  store.setStructuredFilter(field, values)
}

function onEnviarParaConsulta() {
  store.applyCascadeToStructured()
}

function onPesquisar() {
  store.executeStructuredQuery()
}

function clearFilters() {
  store.resetAllFilters()
}

function reload() {
  store.loadCascadeResults()
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
    const current = store.selectedItems || []
    const querySelection = parseSelectionParam(route.query.selection)
    const selectionChanged = !selectionsAreEqual(normalized, current)

    if (selectionChanged) {
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

    await syncChartWithSelection(normalized, { forceLoad: selectionChanged })
  } finally {
    isSyncingSelection = false
  }
}

onMounted(async () => {
  const initialSelection = parseSelectionParam(route.query.selection)

  isSyncingSelection = true
  try {
    const current = store.selectedItems || []
    if (!selectionsAreEqual(initialSelection, current)) {
      store.setSelectedItems(initialSelection)
    }
  } finally {
    isSyncingSelection = false
  }

  const normalizedSelection = store.selectedItems || initialSelection
  await syncChartWithSelection(normalizedSelection, { forceLoad: true })
})

watch(
  () => store.selectedItems,
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
      const companySelection = store.selectedItems || []

      if (!selectionsAreEqual(parsed, companySelection)) {
        store.setSelectedItems(parsed)
      }

      await syncChartWithSelection(parsed)
    } finally {
      isSyncingSelection = false
    }
  },
)

onMounted(() => {
  if (!store.companies.length) {
    reload()
  } else if (!Object.keys(store.facets || {}).length) {
    store.loadCascadeResults()
  }
})
</script>

<style scoped>
.company-search {
  display: grid;
  gap: 32px;
}

.company-search__header h2 {
  margin: 0;
}

.company-search__facets {
  display: grid;
  gap: 24px;
}

.company-search__facets h2 {
  margin: 0;
  font-size: 1.2rem;
}

.company-search__facets > *:not(h2) {
  display: grid;
  gap: 16px;
}

.company-search__query {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.company-search__query textarea {
  min-height: 96px;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--color-border, #d9d9d9);
  font-family: inherit;
  font-size: 0.95rem;
  resize: vertical;
  background-color: #fafafa;
}

.company-search__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.company-search__actions button {
  padding: 10px 16px;
}

.company-search__results {
  display: grid;
  gap: 12px;
}

.company-search__results header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.company-search__status {
  color: #888;
}

.company-search__error {
  color: #d00;
}

.muted {
  color: #777;
}
</style>
