import { defineStore } from 'pinia'
import { fetchChart } from '../services/apiService'

export const useChartStore = defineStore('chart', {
  state: () => ({
    params: {
      type: 'PETR4',
    },
    chart: null,
    isLoading: false,
    error: null,
    lastLoadedTicker: '',
  }),

  actions: {
    setType(type) {
      this.params.type = type || 'PETR4'
    },

    async loadChartByTicker(ticker) {
      const normalized = ticker ? String(ticker) : ''
      const target = normalized || this.params.type || 'PETR4'
      if (target !== this.params.type) {
        this.setType(target)
      } else if (!this.params.type) {
        this.setType('PETR4')
      }

      if (
        this.lastLoadedTicker === this.params.type &&
        this.chart &&
        !this.error
      ) {
        return
      }

      if (this.isLoading && this.params.type === target) {
        return
      }

      await this.loadChart()
    },

    async loadChart() {
      const ticker = this.params.type || 'PETR4'
      this.params.type = ticker
      this.isLoading = true
      this.error = null
      try {
        this.chart = await fetchChart(ticker)
        this.lastLoadedTicker = ticker
      } catch (err) {
        console.error(err)
        this.error = 'Falha ao carregar gráfico'
        this.lastLoadedTicker = ''
      } finally {
        this.isLoading = false
      }
    },
  },
})
