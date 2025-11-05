// src/stores/chartStore.js
import { defineStore } from 'pinia'
import { fetchChart } from '../services/apiService'

export const useChartStore = defineStore('chart', {
  state: () => ({
    selectedType: 'line',
    chart: null,
    isLoading: false,
    error: null,
  }),

  actions: {
    async loadChart(type) {
      const chartType = type || this.selectedType
      this.isLoading = true
      this.error = null

      try {
        const data = await fetchChart(chartType)
        this.chart = data
        this.selectedType = chartType
      } catch (err) {
        this.error = err?.message || 'Erro ao carregar gráfico'
      } finally {
        this.isLoading = false
      }
    },

    setType(type) {
      this.selectedType = type
    },
  },
})
