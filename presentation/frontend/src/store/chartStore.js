import { defineStore } from 'pinia'
import { fetchChart } from '../services/apiService'

function normalizeType(value) {
  return String(value || '').trim()
}

function normalizeSelection(values) {
  if (!Array.isArray(values)) {
    return []
  }
  return values
    .map((item) => String(item || '').trim())
    .filter((item) => item.length)
}

function areSelectionsEqual(a = [], b = []) {
  if (a.length !== b.length) {
    return false
  }
  return a.every((value, index) => value === b[index])
}

export const useChartStore = defineStore('chart', {
  state: () => ({
    params: {
      type: '',
      selection: [],
    },
    chart: null,
    isLoading: false,
    error: null,
  }),

  actions: {
    setType(type) {
      this.params.type = normalizeType(type)
    },

    setSelection(selection) {
      const normalized = normalizeSelection(selection)
      if (areSelectionsEqual(normalized, this.params.selection)) {
        return
      }
      this.params = {
        ...this.params,
        selection: normalized,
      }
    },

    async loadChart() {
      const type = normalizeType(this.params.type)
      if (!type) {
        this.chart = null
        this.error = null
        this.isLoading = false
        return
      }

      this.isLoading = true
      this.error = null
      try {
        const payload = {
          ...this.params,
          type,
        }
        this.chart = await fetchChart(payload)
      } catch (err) {
        console.error(err)
        this.error = err?.message || 'Falha ao carregar gráfico'
      } finally {
        this.isLoading = false
      }
    },
  },
})
