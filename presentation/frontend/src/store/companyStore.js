import { defineStore } from 'pinia'
import { searchCompanies } from '../services/apiService'

const CASCADE_CHAIN = [
  'industry_sector',
  'industry_subsector',
  'industry_segment',
]

const SELECTION_SEPARATOR = '::'

function normalizeValues(values) {
  if (!values) {
    return []
  }
  const array = Array.isArray(values) ? values : [values]
  return array
    .map((value) => String(value ?? '').trim())
    .filter((value) => value.length)
}

function formatValue(value) {
  const raw = String(value ?? '').trim()
  if (!raw) return ''
  if (/[\s,]/.test(raw)) {
    return `"${raw.replace(/"/g, '\\"')}"`
  }
  return raw
}

function buildSelectionValue(company, ticker) {
  return `${company}${SELECTION_SEPARATOR}${ticker}`
}

function splitSelectionValue(value) {
  if (!value || typeof value !== 'string') {
    return { company: '', ticker: '' }
  }
  const [company, ticker] = value.split(SELECTION_SEPARATOR)
  return { company: company || '', ticker: ticker || '' }
}

function facetValues(rawOptions) {
  if (!Array.isArray(rawOptions)) {
    return []
  }
  return rawOptions
    .map((option) => {
      if (option && typeof option === 'object') {
        const value = option.value ?? option.label ?? ''
        return String(value || '').trim()
      }
      if (typeof option === 'boolean') {
        return option ? 'true' : 'false'
      }
      return String(option || '').trim()
    })
    .filter((value) => value.length > 0)
}

function sanitizeFilterMap(filters = {}) {
  const entries = Object.entries(filters)
  if (!entries.length) {
    return {}
  }
  return entries.reduce((acc, [field, values]) => {
    const normalized = normalizeValues(values)
    if (normalized.length) {
      acc[field] = normalized
    }
    return acc
  }, {})
}

export const useCompanyStore = defineStore('company', {
  state: () => ({
    filterQuery: { clauses: [] },
    cascadeFilters: {},
    structuredFilters: {},
    facets: {},
    companies: [],
    total: 0,
    selectedItems: [],
    isLoading: false,
    error: null,
    queryText: '',
  }),

  getters: {
    selectedPairs(state) {
      return (state.selectedItems || []).map(splitSelectionValue)
    },
  },

  actions: {
    setCascadeFacetSelection(field, values) {
      const normalizedField = String(field || '').trim()
      if (!normalizedField) {
        return
      }

      const normalizedValues = normalizeValues(values)
      const nextFilters = { ...this.cascadeFilters }

      if (normalizedValues.length) {
        nextFilters[normalizedField] = normalizedValues
      } else {
        delete nextFilters[normalizedField]
      }

      this.cascadeFilters = nextFilters
      this._normalizeCascadeSelections(normalizedField)
      this.loadCascadeResults()
    },

    async loadCascadeResults() {
      this.isLoading = true
      this.error = null

      try {
        const payload = { filters: sanitizeFilterMap(this.cascadeFilters) }
        const response = await searchCompanies(payload)

        this.companies = response.items || []
        this.total = response.total || 0
        this.facets = response.facets || {}

        this._pruneSelection()
        this._normalizeCascadeSelections(CASCADE_CHAIN[0])
      } catch (err) {
        console.error(err)
        this.error = err?.message || 'Erro ao buscar companhias pela cascata'
      } finally {
        this.isLoading = false
      }
    },

    _normalizeCascadeSelections(changedField) {
      const index = CASCADE_CHAIN.indexOf(changedField)
      if (index === -1) {
        return false
      }

      const nextFilters = { ...this.cascadeFilters }
      let mutated = false

      for (let i = index + 1; i < CASCADE_CHAIN.length; i += 1) {
        const field = CASCADE_CHAIN[i]
        const available = new Set(facetValues(this.facets[field]))
        const current = Array.isArray(nextFilters[field]) ? nextFilters[field] : []

        if (!available.size) {
          if (current.length) {
            delete nextFilters[field]
            mutated = true
          }
          continue
        }

        const filtered = current.filter((value) => available.has(value))

        if (filtered.length !== current.length) {
          if (filtered.length) {
            nextFilters[field] = filtered
          } else {
            delete nextFilters[field]
          }
          mutated = true
        }
      }

      if (mutated) {
        this.cascadeFilters = nextFilters
      }

      return mutated
    },

    setStructuredFilter(field, values) {
      const normalizedField = String(field || '').trim()
      if (!normalizedField) {
        return
      }

      const normalizedValues = normalizeValues(values)
      const nextFilters = { ...this.structuredFilters }

      if (normalizedValues.length) {
        nextFilters[normalizedField] = normalizedValues
      } else {
        delete nextFilters[normalizedField]
      }

      this.structuredFilters = nextFilters
      this._rebuildQueryTextFromStructuredFilters()
    },

    _rebuildQueryTextFromStructuredFilters() {
      const clauses = Object.entries(this.structuredFilters)
        .filter(([, values]) => Array.isArray(values) && values.length)
        .map(([field, values]) => `${field} IN (${values.map(formatValue).join(', ')})`)

      this.queryText = clauses.join(' AND ')
    },

    applyCascadeToStructured() {
      const nextStructured = { ...this.structuredFilters }
      const cascadeEntries = Object.entries(this.cascadeFilters || {})

      for (const [field, values] of cascadeEntries) {
        const normalizedValues = normalizeValues(values)
        if (normalizedValues.length) {
          nextStructured[field] = [...normalizedValues]
        } else {
          delete nextStructured[field]
        }
      }

      this.structuredFilters = nextStructured
      this._rebuildQueryTextFromStructuredFilters()
    },

    async executeStructuredQuery() {
      this.isLoading = true
      this.error = null

      try {
        const payload = { filters: sanitizeFilterMap(this.structuredFilters) }
        const response = await searchCompanies(payload)

        this.companies = response.items || []
        this.total = response.total || 0

        this._pruneSelection()
      } catch (err) {
        console.error(err)
        this.error = err?.message || 'Erro ao executar consulta estruturada'
      } finally {
        this.isLoading = false
      }
    },

    resetCascadeFilters() {
      this.cascadeFilters = {}
      this.loadCascadeResults()
    },

    resetStructuredFilters() {
      this.structuredFilters = {}
      this._rebuildQueryTextFromStructuredFilters()
    },

    resetAllFilters() {
      this.resetCascadeFilters()
      this.resetStructuredFilters()
      this.selectedItems = []
    },

    setSelectedItems(values) {
      const normalized = Array.isArray(values)
        ? values.map((value) => String(value)).filter((value) => value.length)
        : []
      this.selectedItems = normalized
    },

    _pruneSelection() {
      if (!this.selectedItems || this.selectedItems.length === 0) {
        return
      }

      const valid = new Set()
      for (const company of this.companies || []) {
        const companyName = company.company_name || ''
        for (const ticker of company.tickers || []) {
          if (!ticker) continue
          valid.add(buildSelectionValue(companyName, ticker))
        }
      }

      const filtered = this.selectedItems.filter((value) => valid.has(value))
      if (filtered.length !== this.selectedItems.length) {
        this.selectedItems = filtered
      }
    },
  },
})

export { buildSelectionValue, splitSelectionValue }
