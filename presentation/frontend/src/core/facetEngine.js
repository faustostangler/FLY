import { COMPANY_FACETS } from '../config/companyFacets'

export function applyFacetFilters(companies, activeFacetFilters) {
  if (!activeFacetFilters || Object.keys(activeFacetFilters).length === 0) {
    return companies || []
  }

  return (companies || []).filter((company) => {
    for (const [facetKey, values] of Object.entries(activeFacetFilters)) {
      const facet = COMPANY_FACETS.find((entry) => entry.key === facetKey)
      if (!facet) continue

      const selected = Array.isArray(values) ? values : Array.from(values || [])
      if (!selected.length) continue

      const companyValue = company?.[facet.field]
      if (!selected.includes(String(companyValue))) {
        return false
      }
    }
    return true
  })
}

function buildFacetOptions({ companies, facet }) {
  const counts = new Map()

  for (const company of companies || []) {
    let value = company?.[facet.field]
    if (value === null || value === undefined || value === '') continue

    if (Array.isArray(value)) {
      value.forEach((v) => {
        const key = String(v)
        counts.set(key, (counts.get(key) || 0) + 1)
      })
    } else {
      const key = String(value)
      counts.set(key, (counts.get(key) || 0) + 1)
    }
  }

  const options = Array.from(counts.entries()).map(([value, count]) => ({
    value,
    label: value,
    count,
  }))

  options.sort((a, b) => a.label.localeCompare(b.label))

  return options
}

export function recomputeFacets({ companies, activeFacetFilters }) {
  const filteredCompanies = applyFacetFilters(companies || [], activeFacetFilters)

  const facetOptions = {}
  for (const facet of COMPANY_FACETS) {
    facetOptions[facet.key] = buildFacetOptions({
      companies: filteredCompanies,
      facet,
    })
  }

  return {
    filteredCompanies,
    facetOptions,
  }
}

export function buildFacetOptionsFromCompanies(companies) {
  const facetOptions = {}
  for (const facet of COMPANY_FACETS) {
    facetOptions[facet.key] = buildFacetOptions({ companies, facet })
  }
  return facetOptions
}

export { buildFacetOptions }
