<template>
  <section class="company-search company-search--live">
    <header class="company-search__header">
      <h2>Busca ao vivo</h2>
      <div class="company-search__actions">
        <button type="button" class="ghost" @click="clearFilters">Limpar filtros</button>
      </div>
    </header>

    <section class="company-search__facets" aria-labelledby="live-filters-heading">
      <h2 id="live-filters-heading">Filtros</h2>

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
              @click="onRemoveFacetValue(facet.field, value)"
              :aria-label="`Remover filtro ${value}`"
            >
              ×
            </button>
          </span>
        </div>
      </div>
    </section>

    <div class="company-search__results">
      <header>
        <h3>Resultados ({{ total }})</h3>
        <span v-if="isLoading" class="company-search__status">Carregando...</span>
      </header>

      <p v-if="!companies.length && !isLoading" class="muted">
        Nenhuma companhia encontrada com os filtros atuais.
      </p>

      <ul v-else class="company-search__list">
        <li v-for="company in companies" :key="company.code || company.company_name">
          <strong>{{ company.company_name }}</strong>
          <span v-if="company.code" class="company-search__list-ticker">({{ company.code }})</span>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import CompanyFacet from './CompanyFacet.vue'
import { COMPANY_FACETS } from '../config/companyFacets'
import { normalizeFacetKey, useCompanyStore } from '../store/companyStore'

const store = useCompanyStore()
const facetConfigs = COMPANY_FACETS
const draftFacets = ref({})
const DEFAULT_OPERATOR = 'IN'

const companies = computed(() => store.filteredCompanies || [])
const total = computed(() => (store.filteredCompanies || []).length)
const staticFacets = computed(() => store.facets || {})
const dynamicFacetOptions = computed(() => store.dynamicFacetOptions || {})
const isLoading = computed(() => store.isLoading)
const selectedValuesByField = computed(() => store.selectedValuesByField)

function booleanLabel(value) {
  if (value === 'true') return 'Sim'
  if (value === 'false') return 'Não'
  return value
}

function facetOptions(facet) {
  const field = facet.field
  let baseOptions = dynamicFacetOptions.value[field]

  if (!baseOptions || !baseOptions.length) {
    const fallback = staticFacets.value[field] || []
    if (fallback.length) {
      baseOptions = fallback
        .map((value) => {
          const text = String(value ?? '').trim()
          return text ? { value: text, label: text, count: null } : null
        })
        .filter(Boolean)
    }
  }

  if (!baseOptions || !baseOptions.length) {
    baseOptions = Array.isArray(facet.options) ? facet.options : []
  }

  if (facet.type === 'boolean') {
    const defaults = Array.isArray(facet.options) ? facet.options : []
    const normalized = []
    const seen = new Set()

    const pushOption = (rawValue, rawLabel) => {
      if (rawValue === null || rawValue === undefined || rawValue === '') return
      const stringValue = String(rawValue).toLowerCase()
      if (!stringValue) return
      if (seen.has(stringValue)) return
      seen.add(stringValue)
      const label = rawLabel ?? booleanLabel(stringValue)
      normalized.push({ value: stringValue, label })
    }

    for (const option of defaults) {
      if (option && typeof option === 'object') {
        pushOption(option.value ?? option.label ?? '', option.label)
      } else {
        pushOption(option, undefined)
      }
    }

    for (const option of baseOptions || []) {
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
    return Array.isArray(facet.options) ? facet.options : []
  }

  return baseOptions
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

function onFacetDraftChange({ field, values }) {
  const finalValues = Array.isArray(values) ? [...values] : []

  draftFacets.value = {
    ...draftFacets.value,
    [field]: {
      logical: facetLogical(field),
      operator: facetOperator(field),
      values: finalValues,
    },
  }

  store.setPreviewFacet(field, finalValues)
}

function onFacetCommit({ field, logical, values, operator }) {
  const finalLogical = logical || 'AND'
  const finalValues = Array.isArray(values) ? [...values] : []
  const finalOperator = operator || DEFAULT_OPERATOR

  store.setFacetFilter(field, finalLogical, finalValues, finalOperator)

  draftFacets.value = {
    ...draftFacets.value,
    [field]: {
      logical: finalLogical,
      operator: finalOperator,
      values: [],
    },
  }

  store.clearPreviewFacet(field)
  store.loadCompanies()
}

function onRemoveFacetValue(field, value) {
  store.removeFacetValue(field, value)
  store.loadCompanies()
}

function clearFilters() {
  draftFacets.value = {}
  store.resetFilters()
}

onMounted(() => {
  if (!store.companies.length) {
    store.loadCompanies()
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

.company-search__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.company-search__list li {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.company-search__list-ticker {
  color: #475569;
}
</style>
