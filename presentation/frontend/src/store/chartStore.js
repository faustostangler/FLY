import { defineStore } from 'pinia'
import { fetchChart } from '../services/apiService'

export const useChartStore = defineStore('chart', {
  state: () => ({
    params: {
      type: 'test',
    },
    chart: null,
    isLoading: false,
    error: null,
  }),

  actions: {
    setType(type) {
      this.params.type = type || 'test'
    },

    async loadChart() {
      this.isLoading = true
      this.error = null
      try {
        this.chart = await fetchChart(this.params.type)
      } catch (err) {
        console.error(err)
        this.error = 'Falha ao carregar gráfico'
      } finally {
        this.isLoading = false
      }
    },
  },
})
