import { defineStore } from 'pinia'
import { fetchCompanyRatiosChart } from '../services/apiService'
import { buildChartFilterTree } from '../utils/chartFilters'

export const useAccountChartsStore = defineStore('accountCharts', {
  state: () => ({
    companyName: '',
    selectedAccounts: [],
    filterTree: null,
    chart: null,
    isLoading: false,
    error: null,
  }),
  actions: {
    setCompanyName(name) {
      this.companyName = String(name || '').trim()
    },
    setSelectedAccounts(accounts) {
      this.selectedAccounts = Array.isArray(accounts)
        ? accounts.map((code) => String(code || '').trim()).filter(Boolean)
        : []
    },
    setFilterFromFilterQuery(filterQuery) {
      this.filterTree = buildChartFilterTree(filterQuery)
    },
    resetChart() {
      this.chart = null
      this.error = null
    },
    async loadChart() {
      if (!this.companyName) {
        this.error = 'Selecione uma companhia antes de carregar o gráfico'
        this.chart = null
        return
      }
      if (!this.selectedAccounts.length) {
        this.error = 'Selecione ao menos uma conta'
        this.chart = null
        return
      }

      this.isLoading = true
      this.error = null

      try {
        const chart = await fetchCompanyRatiosChart(
          this.companyName,
          this.selectedAccounts,
          this.filterTree,
        )
        this.chart = chart
      } catch (err) {
        console.error(err)
        const message =
          err?.response?.data?.detail || err?.message || 'Falha ao carregar gráfico de ratios'
        this.error = message
        this.chart = null
      } finally {
        this.isLoading = false
      }
    },
  },
})
