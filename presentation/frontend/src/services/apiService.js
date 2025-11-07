import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

export async function fetchChart(type) {
  const res = await api.get(`/charts/${encodeURIComponent(type)}`)
  return res.data
}
