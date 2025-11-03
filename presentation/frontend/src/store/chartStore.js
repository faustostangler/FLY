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
    async updateParams(newParams) {
      this.params = { ...this.params, ...newParams }
      await this.fetchChartData()
    },

    async fetchChartData() {
      this.isLoading = true
      this.error = null
      try {
        const response = await fetchChart(this.params.type)
        this.chart = response
      } catch (err) {
        this.error = 'Erro ao carregar gráfico'
        console.error(err)
      } finally {
        this.isLoading = false
      }
    },
  },
})
