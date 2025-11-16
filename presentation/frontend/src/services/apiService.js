import axios from 'axios'

/**
 * Axios instance configured for the backend.
 * The baseURL should always point to the FastAPI gateway.
 */
const api = axios.create({
  baseURL: 'http://localhost:8000',
})

/**
 * fetchChart
 *
 * High-level API helper to load a generic chart.
 * Steps:
 * 1. Validate the incoming params object.
 * 2. Extract and sanitize the chart type (mandatory).
 * 3. Normalize optional selection array into a CSV query param.
 * 4. Perform GET request against /charts/{type}.
 * 5. Return raw JSON returned by FastAPI.
 */
export async function fetchChart(params) {
  const payload = params || {}
  const type = String(payload.type || '').trim()
  if (!type) {
    throw new Error('Ticker inválido para carregar o gráfico')
  }

  // Normalize "selection" into an array of strings.
  const selection = Array.isArray(payload.selection) ? payload.selection : []

  // Build query string only when useful.
  const query = {}
  if (selection.length) {
    query.selection = selection.join(',')
  }

  // Backend expects encoded type in the URL.
  const res = await api.get(`/charts/${encodeURIComponent(type)}`, {
    params: query,
  })
  return res.data
}

/**
 * fetchAccountLineChart
 *
 * Loads a time-series line chart for a given company ticker and one account code.
 * Steps:
 * 1. Validate ticker and accountCode (both required).
 * 2. Normalize and encode them for safe URL usage.
 * 3. Pass any extra parameters as query params.
 * 4. Return the backend JSON payload.
 */
export async function fetchAccountLineChart(ticker, accountCode, params = {}) {
  const t = String(ticker || '').trim()
  const a = String(accountCode || '').trim()

  if (!t || !a) {
    throw new Error('Ticker e accountCode são obrigatórios')
  }

  const res = await api.get(
    `/api/charts/accounts/line/${encodeURIComponent(t)}`,
    {
      params: {
        account_code: a,
        ...params, // Merges optional filters or time ranges.
      },
    },
  )
  return res.data
}

/**
 * searchCompanies
 *
 * Performs a POST search using a structured filterQuery (SearchFilterTree DTO).
 * Steps:
 * 1. Accept filterQuery or fall back to an empty search structure.
 * 2. Send POST to /companies/search.
 * 3. Return the result list + pagination metadata.
 */
export async function searchCompanies(filterQuery) {
  const res = await api.post('/companies/search', filterQuery || { clauses: [] })
  return res.data
}

/**
 * fetchCompanyFacets
 *
 * Retrieves facet metadata used by filters (industries, sectors, etc.).
 * Pure GET endpoint with no parameters.
 */
export async function fetchCompanyFacets() {
  const res = await api.get('/companies/facets')
  return res.data
}

/**
 * fetchCompanyRatiosChart
 *
 * Loads a multi-account ratios chart for a company.
 * Steps:
 * 1. Validate the company name (mandatory).
 * 2. Normalize and sanitize account codes.
 * 3. Reject empty account list.
 * 4. Optionally include the filterTree (SearchFilterTree) as a nested object.
 * 5. POST the payload to /api/charts/ratios/company.
 */
export async function fetchCompanyRatiosChart(companyName, accounts, filterTree = null) {
  const name = String(companyName || '').trim()
  if (!name) {
    throw new Error('Nome da companhia é obrigatório para carregar o gráfico de ratios')
  }

  // Convert and sanitize all account codes.
  const normalizedAccounts = Array.isArray(accounts)
    ? accounts.map((code) => String(code || '').trim()).filter(Boolean)
    : []

  if (!normalizedAccounts.length) {
    throw new Error('Selecione pelo menos uma conta para carregar o gráfico')
  }

  // Backend expects a structured payload including optional filters.
  const payload = {
    company_name: name,
    accounts: normalizedAccounts,
    filters: filterTree ? { tree: filterTree } : null,
  }

  const res = await api.post('/api/charts/ratios/company', payload)
  return res.data
}
