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

export async function searchCompanies(payload) {
  const body = payload && typeof payload === 'object' ? payload : {}
  const res = await api.post('/companies/search', body)
  return res.data
}

export async function fetchCompanyFacets() {
  const res = await api.get('/companies/facets')
  return res.data
}
