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
          :logical="'AND'"
          :operator="facetOperator(facet.field)"
          :values="facetValues(facet.field)"
          :multiple="facet.multiple !== false"
          :type="facet.type || 'text'"
          :searchable="Boolean(facet.searchable)"
          @change="onFacetChange"
        />

        <div
          v-if="facetSelectedValues(facet.field).length"
          class="company-facet__selected"
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
              aria-label="Remover filtro"
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
import { computed, onMounted } from 'vue'
import { COMPANY_FACETS } from '../config/companyFacets'
import { useCompanyStore } from '../store/companyStore'
import CompanyFacet from './CompanyFacet.vue'
import CompanyResultSelect from './CompanyResultSelect.vue'

const store = useCompanyStore()
const facetConfigs = COMPANY_FACETS
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

const companies = computed(() => store.companies)
const total = computed(() => store.total)
const staticFacets = computed(() => store.facets || {})
const dynamicFacetOptions = computed(() => store.dynamicFacetOptions || {})
const isLoading = computed(() => store.isLoading)
const error = computed(() => store.error)
const selectedValuesByField = computed(() => store.selectedValuesByField)

const selectedItemsModel = computed({
  get: () => store.selectedItems,
  set: (values) => {
    const normalized = Array.isArray(values)
      ? values.map((value) => String(value)).filter((value) => value.length)
      : []
    store.setSelectedItems(normalized)
  },
})

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
    baseOptions = fallback.map((value) => ({
      value: String(value),
      label: String(value),
      count: null,
    }))
  }

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
    return facet.options || []
  }

  const normalizedOptions = (baseOptions || [])
    .map((option) => {
      if (option && typeof option === 'object') {
        const value = String(option.value ?? option.label ?? '').trim()
        if (!value) return null
        const label = option.label ?? value
        const count = option.count ?? null
        return { value, label, count }
      }
      const value = String(option || '').trim()
      if (!value) return null
      return { value, label: value, count: null }
    })
    .filter(Boolean)

  if (!isCascadeField(field)) {
    return normalizedOptions
  }

  const cascade = store.industryCascade || {}
  return applyIndustryCascade(field, normalizedOptions, cascade, {
    selectedSectors: currentCascadeValues('industry_sector'),
    selectedSubsectors: currentCascadeValues('industry_subsector'),
  })
}

function applyIndustryCascade(field, options, cascade, { selectedSectors, selectedSubsectors }) {
  const { sectorToSubsectors = {}, sectorToSegments = {}, subsectorToSegments = {} } = cascade

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
    return options
  }

  const allowedSet = new Set(allowedValues.map((value) => String(value || '').trim()))

  return options.filter((option) =>
    allowedSet.has(String(option.value || '').trim()),
  )
}

function currentCascadeValues(field) {
  const committed = store.clauseByField[field]?.condition?.values || []
  return committed
    .map((value) => String(value || '').trim())
    .filter(Boolean)
}

function facetOperator(field) {
  return store.clauseByField[field]?.condition?.operator || DEFAULT_OPERATOR
}

function facetValues(field) {
  return store.clauseByField[field]?.condition?.values || []
}

function facetSelectedValues(field) {
  return selectedValuesByField.value[field] || []
}

function removeFacetValue(field, valueToRemove) {
  const current = selectedValuesByField.value[field] || []
  const next = current.filter((value) => value !== valueToRemove)

  store.setFacetSelection(field, 'AND', next, DEFAULT_OPERATOR)
  store.loadCompanies()
}

function onFacetChange({ field, logical, values, operator }) {
  const finalValues = Array.isArray(values) ? [...values] : []
  const finalOperator = operator || DEFAULT_OPERATOR

  store.setFacetSelection(field, 'AND', finalValues, finalOperator)
  store.loadCompanies()
}

function clearFilters() {
  store.resetFiltersAndReload()
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
  gap: 1rem;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.company-search__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.company-search--live {
  gap: 1.5rem;
}

.company-search__facet {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.company-facet__selected {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.company-facet__chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.5rem;
  background: #e2e8f0;
  border-radius: 999px;
  font-size: 0.9rem;
}

.company-facet__chip-remove {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
}
</style>
