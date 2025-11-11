import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

export async function fetchChart(params) {
  const payload = params || {}
  const type = String(payload.type || '').trim()
  if (!type) {
    throw new Error('Ticker inválido para carregar o gráfico')
  }
  const selection = Array.isArray(payload.selection) ? payload.selection : []

  const query = {}
  if (selection.length) {
    query.selection = selection.join(',')
  }

  const res = await api.get(`/charts/${encodeURIComponent(type)}`, {
    params: query,
  })
  return res.data
}

export async function searchCompanies(filterQuery) {
  const res = await api.post('/companies/search', filterQuery || { clauses: [] })
  return res.data
}

export async function fetchCompanyFacets() {
  const res = await api.get('/companies/facets')
  return res.data
}

export async function fetchCompanyRatiosChart(companyName, accounts, filterTree = null) {
  const name = String(companyName || '').trim()
  if (!name) {
    throw new Error('Nome de companhia inválido para carregar gráficos de ratios')
  }

  const normalizedAccounts = Array.isArray(accounts)
    ? accounts.map((code) => String(code || '').trim()).filter(Boolean)
    : []

  if (!normalizedAccounts.length) {
    throw new Error('É necessário informar ao menos uma conta')
  }

  const payload = {
    company_name: name,
    accounts: normalizedAccounts,
    filters: filterTree ? { tree: filterTree } : null,
  }

  const res = await api.post('/api/charts/ratios/company', payload)
  return res.data
}
