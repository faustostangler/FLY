<template>
  <section class="company-search">
    <header class="company-search__header">
      <h2>Construtor de filtros</h2>
      <div class="company-search__actions">
      </div>
    </header>

    <section class="company-search__facets" aria-labelledby="filters-heading">
      <h2 id="filters-heading">Filtros</h2>

      <div
        v-for="facet in facetConfigs"
        :key="facet.field"
        class="company-search__facet"
      >
        <CompanyFacet
          :field="facet.field"
          :label="facet.label"
          :options="facetOptions(facet)"
          :logical="facetLogical(facet.field)"
          :operator="facetOperator(facet.field)"
          :values="facetValues(facet.field)"
          :multiple="facet.multiple !== false"
          :type="facet.type || 'text'"
          :searchable="Boolean(facet.searchable)"
          @change="onFacetDraftChange"
          @commit="onFacetCommit"
        />

        <div
          v-if="facetSelectedValues(facet.field).length"
          class="company-search__facet-selection"
        >
          <span
            v-for="value in facetSelectedValues(facet.field)"
            :key="value"
            class="company-facet__chip"
          >
            {{ value }}
            <button
              type="button"
              class="company-facet__chip-remove"
              @click="removeFacetValue(facet.field, value)"
            >
              ×
            </button>
          </span>
        </div>
      </div>
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
        <button type="button" @click="applyQuery">Buscar</button>
        <button type="button" class="ghost" @click="clearFilters">Limpar filtros</button>
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
import { normalizeFacetKey, useCompanyStore } from '../store/companyStore'
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
const parseError = ref('')
const draftFacets = ref({})
const DEFAULT_OPERATOR = 'IN'

const CASCADE_CONFIG = {
  industry_sector: {
    level: 'sector',
    parentField: null,
  },
  industry_subsector: {
    level: 'subsector',
    parentField: 'industry_sector',
  },
  industry_segment: {
    level: 'segment',
    parentField: 'industry_subsector',
  },
}

const CASCADE_FIELDS = Object.keys(CASCADE_CONFIG)

function isCascadeField(field) {
  return CASCADE_FIELDS.includes(field)
}

const queryTextModel = computed({
  get: () => store.queryText,
  set: (value) => {
    parseError.value = ''
    store.setQueryText(value)
  },
})

const companies = computed(() => store.filteredCompanies || [])
const total = computed(() => (store.filteredCompanies || []).length)
const facets = computed(() => store.facets || {})
// const staticFacets = computed(() => store.facets || {})
// const dynamicFacetOptions = computed(() => store.dynamicFacetOptions || {})
const isLoading = computed(() => store.isLoading)
const error = computed(() => store.error)
const selectedValuesByField = computed(() => store.selectedValuesByField)

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

  const baseOptions = dynamic.length ? dynamic : (facet.options || [])

  if (!isCascadeField(field)) {
    return baseOptions
  }

  const cascade = store.industryCascade || {}
  const { sectorToSubsectors = {}, sectorToSegments = {}, subsectorToSegments = {} } = cascade

  const selectedSectors = currentCascadeValues('industry_sector')
  const selectedSubsectors = currentCascadeValues('industry_subsector')

  let allowedValues = null

  if (field === 'industry_sector') {
    const sectorsFromGraph = Object.keys(sectorToSubsectors).length
      ? Object.keys(sectorToSubsectors)
      : Object.keys(sectorToSegments)

    if (sectorsFromGraph.length) {
      allowedValues = sectorsFromGraph
    }
  } else if (field === 'industry_subsector') {
    const sectors = selectedSectors.length
      ? selectedSectors
      : Object.keys(sectorToSubsectors)

    const aggregated = new Set()
    for (const sector of sectors) {
      for (const subsector of sectorToSubsectors[sector] || []) {
        aggregated.add(subsector)
      }
    }
    if (aggregated.size) {
      allowedValues = Array.from(aggregated)
    }
  } else if (field === 'industry_segment') {
    const aggregated = new Set()

    if (selectedSubsectors.length) {
      for (const subsector of selectedSubsectors) {
        for (const segment of subsectorToSegments[subsector] || []) {
          aggregated.add(segment)
        }
      }
    } else if (selectedSectors.length) {
      for (const sector of selectedSectors) {
        for (const segment of sectorToSegments[sector] || []) {
          aggregated.add(segment)
        }
      }
    } else {
      for (const key of Object.keys(subsectorToSegments)) {
        for (const segment of subsectorToSegments[key] || []) {
          aggregated.add(segment)
        }
      }
    }

    if (aggregated.size) {
      allowedValues = Array.from(aggregated)
    }
  }

  if (!allowedValues || !allowedValues.length) {
    // Sem restrição de cascata calculada: devolve a lista original
    return baseOptions
  }

  // Aqui a cascata entra em ação de fato
  const allowedSet = new Set(
    allowedValues.map((value) => String(value || '').trim()),
  )

  // Garante que todas as opções sejam { value, label }
  const normalized = baseOptions.map((option) => {
    if (option && typeof option === 'object') {
      const value = String(option.value ?? option.label ?? '').trim()
      const label = option.label ?? value
      return { value, label }
    }
    const value = String(option || '').trim()
    return { value, label: value }
  })

  return normalized.filter((option) =>
    allowedSet.has(String(option.value || '').trim()),
  )
}

function currentCascadeValues(field) {
  const committed = store.clauseByField[field]?.condition?.values || []
  const draft = draftFacets.value[field]?.values || []
  const all = [...committed, ...draft]
    .map((value) => String(value || '').trim())
    .filter(Boolean)

  const seen = new Set()
  const result = []
  for (const value of all) {
    if (seen.has(value)) continue
    seen.add(value)
    result.push(value)
  }
  return result
}

function facetLogical(field) {
  const draft = draftFacets.value[field]
  if (draft && draft.logical) {
    return draft.logical
  }
  return store.clauseByField[field]?.logical || 'AND'
}

function facetOperator(field) {
  const draft = draftFacets.value[field]
  if (draft && draft.operator) {
    return draft.operator
  }
  return store.clauseByField[field]?.condition?.operator || ''
}

function facetValues(field) {
  const draft = draftFacets.value[field]
  if (draft && Array.isArray(draft.values)) {
    return draft.values
  }
  return store.clauseByField[field]?.condition?.values || []
}

function facetSelectedValues(field) {
  const key = normalizeFacetKey(field)
  if (!key) return []
  const values = selectedValuesByField.value[key]
  return Array.isArray(values) ? values : []
}

function onFacetDraftChange({ field, logical, values, operator }) {
  const finalValues = Array.isArray(values) ? [...values] : []

  draftFacets.value = {
    ...draftFacets.value,
    [field]: {
      logical: logical || 'AND',
      operator: operator || '',
      values: finalValues,
    },
  }

  store.setPreviewFacet(field, finalValues)
}

function onFacetCommit({ field, logical, values, operator }) {
  const finalLogical = logical || 'AND'
  const finalValues = Array.isArray(values) ? [...values] : []
  const finalOperator = operator || DEFAULT_OPERATOR

  // “Enviar para consulta” atua só no builder
  store.setBuilderFacet(field, finalLogical, finalValues, finalOperator)

  draftFacets.value = {
    ...draftFacets.value,
    [field]: {
      logical: finalLogical,
      operator: finalOperator,
      values: [],
    },
  }

  store.clearPreviewFacet(field)
}

function removeFacetValue(field, value) {
  store.removeFacetValue(field, value)
  store.loadCompanies()
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
  }
  if (!Object.keys(store.facets || {}).length) {
    store.loadFacets()
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
  /* background-color: var(--vt-c-bg-mute, #e9f3fd); */
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

.company-search__facet {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.company-search__facet-selection {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.company-facet__chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background-color: #e2e8f0;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  padding: 0.15rem 0.45rem 0.15rem 0.65rem;
  font-size: 0.9rem;
}

.company-facet__chip-remove {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  color: #0f172a;
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
