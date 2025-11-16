<template>
  <!--
    Main company search builder layout.

    This section groups:
    - Header title and actions
    - Facet-based filter controls
    - Structured query textarea
    - Result list with selection widget
  -->
  <section class="company-search">
    <header class="company-search__header">
      <h2>Construtor de filtros</h2>
      <div class="company-search__actions">
        <!-- Reserved for future actions (e.g., save/load presets) -->
      </div>
    </header>

    <!--
      Facet-based filter area.

      Each CompanyFacet represents one field that can be filtered,
      wired to the store via helper functions below.
    -->
    <section class="company-search__facets" aria-labelledby="filters-heading">
      <h2 id="filters-heading">Filtros</h2>

      <CompanyFacet
        v-for="facet in facetConfigs"
        :key="facet.field"
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
    </section>

    <!--
      Structured query editor.

      Mirrors and controls the same filter state as the facets,
      but expressed as a string for advanced users.
    -->
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
        <!-- <button type="button" @click="reload">Buscar</button> -->
        <span v-if="parseError" class="company-search__error">{{ parseError }}</span>
      </div>
    </div>

    <!--
      Result list and selection.

      Selection here is the single source of truth that also drives
      URL query string and chart synchronization.
    -->
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
import { extractTickers } from '../utils/tickers'
import CompanyFacet from './CompanyFacet.vue'
import CompanyResultSelect from './CompanyResultSelect.vue'

// Pinia stores for companies and charts
const store = useCompanyStore()
const chartStore = useChartStore()

// Router objects for reading/writing URL query string
const route = useRoute()
const router = useRouter()

// Guard flag to prevent infinite sync loops between watchers
let isSyncingSelection = false

// Static facet definitions coming from configuration
const facetConfigs = COMPANY_FACETS

// Error message for structured query parsing
const parseError = ref('')

// Local buffer for facet drafts (before user commits them)
const draftFacets = ref({})

// Default operator used when user does not explicitly choose one
const DEFAULT_OPERATOR = 'IN'

// ---------------------------------------------------------------------------
// Industry cascade configuration
// ---------------------------------------------------------------------------

/**
 * CASCADE_CONFIG describes how the industry hierarchy is structured
 * (sector -> subsector -> segment) and how fields depend on each other.
 *
 * Each entry defines:
 * - level: the conceptual level in the hierarchy
 * - parentField: the field above it that constrains its options
 */
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

// Convenient list of fields that participate in the cascade
const CASCADE_FIELDS = Object.keys(CASCADE_CONFIG)

/**
 * Returns true when the given field belongs to the industry cascade.
 *
 * @param {string} field - Field name to check.
 * @returns {boolean} Whether the field participates in the cascade.
 */
function isCascadeField(field) {
  return CASCADE_FIELDS.includes(field)
}

// ---------------------------------------------------------------------------
// Query text computed model
// ---------------------------------------------------------------------------

/**
 * Computed wrapper around the store's queryText.
 *
 * - get: reads the current structured query string from the store
 * - set: clears local parse errors and forwards the new value to the store
 */
const queryTextModel = computed({
  get: () => store.queryText,
  set: (value) => {
    // Reset parse errors whenever the user types a new query
    parseError.value = ''
    store.setQueryText(value)
  },
})

// ---------------------------------------------------------------------------
// Basic computed bindings to the store
// ---------------------------------------------------------------------------

const companies = computed(() => store.companies)
const total = computed(() => store.total)
const facets = computed(() => store.facets || {})
const isLoading = computed(() => store.isLoading)
const error = computed(() => store.error)

/**
 * Computed v-model for selected companies.
 *
 * - get: reads selection from the company store
 * - set: forwards changes to the selection synchronization handler
 */
const selectedItemsModel = computed({
  get: () => store.selectedItems,
  set: (values) => {
    onSelectionChange(values)
  },
})

// ---------------------------------------------------------------------------
// Selection utilities
// ---------------------------------------------------------------------------

/**
 * Normalize a selection array:
 * - Ensure the result is an array
 * - Coerce all values to trimmed strings
 * - Remove empty entries
 *
 * @param {Array<unknown>} values - Raw selection values.
 * @returns {string[]} Normalized selection values.
 */
function normalizeSelection(values) {
  if (!Array.isArray(values)) {
    return []
  }
  return values
    .map((value) => String(value || '').trim())
    .filter((value) => value.length)
}

/**
 * Parse a "selection" parameter from the query string.
 *
 * Steps:
 * 1. Accept either a single value or an array of values
 * 2. Split values by comma
 * 3. Trim and filter out empty entries
 *
 * @param {string|string[]|undefined} rawValue - Raw query parameter.
 * @returns {string[]} Parsed normalized selection.
 */
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

/**
 * Shallow comparison of two selection arrays.
 * Assumes order is meaningful and expected to match.
 *
 * @param {string[]} [a=[]] - First selection.
 * @param {string[]} [b=[]] - Second selection.
 * @returns {boolean} Whether both arrays have the same length and elements.
 */
function selectionsAreEqual(a = [], b = []) {
  if (a.length !== b.length) {
    return false
  }
  return a.every((value, index) => value === b[index])
}

// ---------------------------------------------------------------------------
// Facet helpers
// ---------------------------------------------------------------------------

/**
 * Translate a boolean value string into a user-friendly label.
 *
 * @param {string} value - Raw string ("true" / "false").
 * @returns {string} Human readable label.
 */
function booleanLabel(value) {
  if (value === 'true') return 'Sim'
  if (value === 'false') return 'Não'
  return value
}

/**
 * Build the available options for a given facet.
 *
 * Responsibilities:
 * 1. Merge static options (from config) with dynamic options (from store)
 * 2. Normalize options into { value, label } objects
 * 3. Handle special types (boolean, date-range)
 * 4. For cascade fields, restrict options to those allowed by the cascade graph
 *
 * @param {object} facet - Facet configuration object.
 * @returns {Array<{value: string, label: string}>} Resolved options.
 */
function facetOptions(facet) {
  const field = facet.field
  const dynamic = facets.value[field] || []

  // Special handling for boolean facets to avoid duplicated or invalid values
  if (facet.type === 'boolean') {
    const base = Array.isArray(facet.options) ? facet.options : []
    const normalized = []
    const seen = new Set()

    /**
     * Register a single boolean option, ensuring uniqueness and normalization.
     *
     * @param {unknown} rawValue - Raw option value (can be object/boolean/string).
     * @param {string|undefined} rawLabel - Optional label override.
     */
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

    // Step 1: process configured base options
    for (const option of base) {
      if (option && typeof option === 'object') {
        pushOption(option.value ?? option.label ?? '', option.label)
      } else {
        pushOption(option, undefined)
      }
    }

    // Step 2: process dynamic options from backend
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

  // Date-range facets simply reuse options defined in config
  if (facet.type === 'date-range') {
    return facet.options || []
  }

  // For generic facets, start from dynamic or fallback to static options
  const baseOptions = dynamic.length ? dynamic : (facet.options || [])

  // If this facet does not participate in the cascade, return as-is
  if (!isCascadeField(field)) {
    return baseOptions
  }

  // -----------------------------------------------------------------------
  // Cascade filtering logic for industry_* fields
  // -----------------------------------------------------------------------

  const cascade = store.industryCascade || {}
  const { sectorToSubsectors = {}, sectorToSegments = {}, subsectorToSegments = {} } = cascade

  // Read committed + draft selections in the cascade
  const selectedSectors = currentCascadeValues('industry_sector')
  const selectedSubsectors = currentCascadeValues('industry_subsector')

  let allowedValues = null

  // 1) Sector: use graph keys as allowed sectors if present
  if (field === 'industry_sector') {
    const sectorsFromGraph = Object.keys(sectorToSubsectors).length
      ? Object.keys(sectorToSubsectors)
      : Object.keys(sectorToSegments)

    if (sectorsFromGraph.length) {
      allowedValues = sectorsFromGraph
    }
  // 2) Subsector: derive from selected sectors or all sectors
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
  // 3) Segment: derive from selected subsectors, then from sectors, then from whole graph
  } else if (field === 'industry_segment') {
    const aggregated = new Set()

    if (selectedSubsectors.length) {
      // a) subsectors selected: union segments across selected subsectors
      for (const subsector of selectedSubsectors) {
        for (const segment of subsectorToSegments[subsector] || []) {
          aggregated.add(segment)
        }
      }
    } else if (selectedSectors.length) {
      // b) sectors selected: union segments across sectors
      for (const sector of selectedSectors) {
        for (const segment of sectorToSegments[sector] || []) {
          aggregated.add(segment)
        }
      }
    } else {
      // c) nothing selected: allow all segments from the entire graph
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

  // If the cascade graph does not constrain anything, keep original options
  if (!allowedValues || !allowedValues.length) {
    // No cascade restriction calculated: return original list
    return baseOptions
  }

  // At this point the cascade actually filters the options
  const allowedSet = new Set(
    allowedValues.map((value) => String(value || '').trim()),
  )

  // Normalize every option to { value, label } form
  const normalized = baseOptions.map((option) => {
    if (option && typeof option === 'object') {
      const value = String(option.value ?? option.label ?? '').trim()
      const label = option.label ?? value
      return { value, label }
    }
    const value = String(option || '').trim()
    return { value, label: value }
  })

  // Keep only options whose value is allowed by the cascade constraints
  return normalized.filter((option) =>
    allowedSet.has(String(option.value || '').trim()),
  )
}

/**
 * Resolve the logical operator (AND/OR) for a given field.
 * Prefers draft value, then falls back to store's committed clause.
 *
 * @param {string} field - Facet field name.
 * @returns {string} Logical operator to use.
 */
function facetLogical(field) {
  const draft = draftFacets.value[field]
  if (draft && draft.logical) {
    return draft.logical
  }
  return store.clauseByField[field]?.logical || 'AND'
}

/**
 * Resolve the comparison operator for a given field.
 * Prefers draft value, then falls back to store's committed clause.
 *
 * @param {string} field - Facet field name.
 * @returns {string} Operator to use (e.g., IN, =, >=).
 */
function facetOperator(field) {
  const draft = draftFacets.value[field]
  if (draft && draft.operator) {
    return draft.operator
  }
  return store.clauseByField[field]?.condition?.operator || ''
}

/**
 * Resolve the values for a given field.
 * Prefers draft values, then falls back to store's committed values.
 *
 * @param {string} field - Facet field name.
 * @returns {any[]} Array of facet values.
 */
function facetValues(field) {
  const draft = draftFacets.value[field]
  if (draft && Array.isArray(draft.values)) {
    return draft.values
  }
  return store.clauseByField[field]?.condition?.values || []
}

/**
 * Compute the current cascade values for a given field.
 *
 * Steps:
 * 1. Read committed values from store
 * 2. Read draft values from local state
 * 3. Merge both, normalize to trimmed strings
 * 4. Deduplicate while preserving order
 *
 * @param {string} field - Cascade field name.
 * @returns {string[]} Unique merged values.
 */
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

/**
 * Handle transient changes to a facet (before commit).
 *
 * This keeps an in-memory snapshot so the user can adjust
 * values without immediately affecting the committed filters.
 *
 * @param {object} payload - Change event from CompanyFacet.
 */
function onFacetDraftChange({ field, logical, values, operator }) {
  draftFacets.value = {
    ...draftFacets.value,
    [field]: {
      logical: logical || 'AND',
      operator: operator || '',
      values: Array.isArray(values) ? [...values] : [],
    },
  }
}

/**
 * Handle committed changes from a facet.
 *
 * Steps:
 * 1. Normalize logical/operator/values
 * 2. Persist them to the store via setFacetSelection
 * 3. Clear local draft values (but keep the structural metadata)
 *
 * @param {object} payload - Commit event from CompanyFacet.
 */
function onFacetCommit({ field, logical, values, operator }) {
  const finalLogical = logical || 'AND'
  const finalValues = Array.isArray(values) ? [...values] : []
  const finalOperator = operator || DEFAULT_OPERATOR

  // 1) Update the global filter state in the store
  store.setFacetSelection(field, finalLogical, finalValues, finalOperator)

  // 2) Reset the local draft values for this field
  draftFacets.value = {
    ...draftFacets.value,
    [field]: {
      logical: finalLogical,
      operator: finalOperator,
      values: [],
    },
  }
}

/**
 * Apply the structured query currently in the store.
 *
 * Steps:
 * 1. Ask the store to parse and apply queryText
 * 2. If parsing fails, expose human readable error message
 * 3. If success, clear any previous parse error
 */
function applyQuery() {
  const result = store.applyQueryText()
  if (!result.ok) {
    parseError.value = result.message || 'Não foi possível interpretar a consulta.'
    return
  }
  parseError.value = ''
}

/**
 * Reset all filters to their default state.
 *
 * Steps:
 * 1. Ask the store to reset its filter state
 * 2. Clear local parse error
 * 3. Clear local draft facets
 */
function clearFilters() {
  store.resetFilters()
  parseError.value = ''
  draftFacets.value = {}
}

/**
 * Trigger a reload of companies from the backend
 * using the current filters in the store.
 */
function reload() {
  store.loadCompanies()
}

/**
 * Synchronize the chart store with a given selection of companies.
 *
 * Concept:
 * - The first ticker is the "primary" and becomes the chart "type"
 * - Remaining tickers become the comparison selection
 *
 * Steps:
 * 1. Extract tickers from selection values
 * 2. Derive primary and comparison tickers
 * 3. Check if chart type or selection changed
 * 4. Update chart store if needed
 * 5. Load chart if forced or if any parameter changed
 *
 * @param {string[]} selectionValues - Current company selection.
 * @param {object} [options] - Additional options.
 * @param {boolean} [options.forceLoad=false] - Whether to force chart reload.
 */
async function syncChartWithSelection(selectionValues, { forceLoad = false } = {}) {
  // 1) Extract tickers from user-friendly selection values
  const tickers = extractTickers(selectionValues)
  const [primaryTicker, ...comparisonTickers] = tickers

  // 2) Read current chart params
  const currentType = chartStore.params.type || ''
  const currentSelection = chartStore.params.selection || []

  // 3) Detect if type or selection actually changed
  const typeChanged = primaryTicker !== currentType
  const selectionChanged = !selectionsAreEqual(comparisonTickers, currentSelection)

  // 4) Apply changes to chart params
  if (typeChanged) {
    chartStore.setType(primaryTicker)
  }
  if (selectionChanged) {
    chartStore.setSelection(comparisonTickers)
  }

  // 5) Load chart only when needed
  if (forceLoad || typeChanged || selectionChanged) {
    await chartStore.loadChart()
  }
}

/**
 * Central handler for selection changes coming from the UI.
 *
 * Responsibilities:
 * - Normalize selection
 * - Keep Pinia store state in sync
 * - Keep URL query parameter "selection" in sync
 * - Trigger chart synchronization
 * - Avoid infinite loops with a local guard flag
 *
 * @param {Array<unknown>} values - New selection values from v-model.
 */
async function onSelectionChange(values) {
  // Prevent recursion when we are already syncing selection
  if (isSyncingSelection) {
    return
  }

  isSyncingSelection = true

  try {
    // 1) Normalize incoming selection
    const normalized = normalizeSelection(values)
    const current = store.selectedItems || []
    const querySelection = parseSelectionParam(route.query.selection)
    const selectionChanged = !selectionsAreEqual(normalized, current)

    // 2) Update Pinia store if actual change occurred
    if (selectionChanged) {
      store.setSelectedItems(normalized)
    }

    // 3) Build query string representation for the router
    const selectionParam = normalized.join(',')
    const nextQuery = {
      ...route.query,
      selection: selectionParam || undefined,
    }

    // 4) Push changes to the URL if they differ from current query
    if (!selectionsAreEqual(normalized, querySelection)) {
      try {
        await router.replace({ query: nextQuery })
      } catch (error) {
        // Routing errors are logged but do not break user flow
        console.error(error)
      }
    }

    // 5) Keep chart state in sync with the new selection
    await syncChartWithSelection(normalized, { forceLoad: selectionChanged })
  } finally {
    // Always release the guard flag
    isSyncingSelection = false
  }
}

// ---------------------------------------------------------------------------
// Initial mount: read URL selection and sync chart
// ---------------------------------------------------------------------------

onMounted(async () => {
  // 1) Read initial selection from URL query string
  const initialSelection = parseSelectionParam(route.query.selection)

  isSyncingSelection = true
  try {
    // 2) Align store selection with URL if necessary
    const current = store.selectedItems || []
    if (!selectionsAreEqual(initialSelection, current)) {
      store.setSelectedItems(initialSelection)
    }
  } finally {
    isSyncingSelection = false
  }

  // 3) Compute final selection and trigger initial chart load
  const normalizedSelection = store.selectedItems || initialSelection
  await syncChartWithSelection(normalizedSelection, { forceLoad: true })
})

// ---------------------------------------------------------------------------
// Watchers to keep Store, URL, and Charts in sync
// ---------------------------------------------------------------------------

/**
 * Watcher: reacts to changes in store.selectedItems.
 *
 * Scenario:
 * - User changes selection via UI or another piece of code
 *
 * Responsibilities:
 * 1. Normalize selection
 * 2. If URL query is out of sync, use central handler to fix everything
 * 3. Otherwise, only synchronize chart state
 */
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

/**
 * Watcher: reacts to changes in route.query.selection.
 *
 * Scenario:
 * - User changes URL manually
 * - Navigation/back/forward modifies selection in the query string
 *
 * Responsibilities:
 * 1. Parse selection from URL
 * 2. Align store selection with URL
 * 3. Synchronize charts accordingly
 */
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

// ---------------------------------------------------------------------------
// Additional mount hook: ensure companies and facets are loaded
// ---------------------------------------------------------------------------

onMounted(() => {
  // Ensure companies are loaded at least once
  if (!store.companies.length) {
    reload()
  }
  // Ensure facet metadata is available for filters
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
