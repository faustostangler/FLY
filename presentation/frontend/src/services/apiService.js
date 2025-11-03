import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

export async function fetchChart(type) {
  const response = await api.get(`/api/charts/${encodeURIComponent(type)}`)
  return response.data
}
