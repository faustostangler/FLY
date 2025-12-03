// presentation/frontend/src/store/accountChartsStore.js
import { defineStore } from 'pinia'

import { fetchCompanyRatiosChart } from '../services/apiService'
import { buildChartFilterTree } from '../utils/chartFilters'

export const useAccountChartsStore = defineStore('accountCharts', {
  state: () => ({
    companies: [],          // [{ company, ticker }]
    selectedAccounts: [],   // ['02.03', '03.01', ...]
    filterTree: null,       // árvore de filtros
    chartsByAccount: {},    // { '02.03': ChartDTO, '03.01': ChartDTO, ... }
    isLoading: false,
    error: null,
  }),

  actions: {
    setCompanies(pairs) {
      this.companies = Array.isArray(pairs)
        ? pairs
            .map((p) => ({
              company: String(p.company || '').trim(),
              ticker: String(p.ticker || '').trim(),
            }))
            .filter((p) => p.company)
        : []
    },

    setSelectedAccounts(accounts) {
      this.selectedAccounts = Array.isArray(accounts)
        ? accounts.map((code) => String(code || '').trim()).filter(Boolean)
        : []
    },

    setFilterFromFilterQuery(filterQuery) {
      this.filterTree = buildChartFilterTree(filterQuery)
    },

    resetCharts() {
      this.chartsByAccount = {}
      this.error = null
    },

    async loadCharts() {
      if (!this.companies.length) {
        this.error =
          'Selecione ao menos uma companhia antes de visualizar os gráficos'
        this.chartsByAccount = {}
        return
      }

      if (!this.selectedAccounts.length) {
        this.error = 'Selecione ao menos uma conta para exibir'
        this.chartsByAccount = {}
        return
      }

      this.isLoading = true
      this.error = null
      this.chartsByAccount = {}

      try {
        const results = {}

        // 1 gráfico por account
        for (const accountCode of this.selectedAccounts) {
          const chart = await this._loadChartForAccount(accountCode)
          results[accountCode] = chart
        }

        this.chartsByAccount = results
      } catch (err) {
        console.error(err)
        const message =
          err?.response?.data?.detail ||
          err?.message ||
          'Falha ao carregar gráficos de ratios'
        this.error = message
        this.chartsByAccount = {}
      } finally {
        this.isLoading = false
      }
    },

    async _loadChartForAccount(accountCode) {
      const traces = []
      let baseLayout = null
      let baseMeta = null

      for (const pair of this.companies) {
        const companyName = pair.company
        const ticker = pair.ticker

        // Backend continua consumindo 1 empresa + 1 conta
        const dto = await fetchCompanyRatiosChart(
          companyName,
          [accountCode],
          this.filterTree,
        )

        if (!baseLayout) {
          baseLayout = { ...(dto.layout || {}) }
          baseMeta = { ...(dto.meta || {}) }
        }

        const [trace] = Array.isArray(dto.data) ? dto.data : []
        if (!trace) continue

        traces.push({
          ...trace,
          name: ticker ? `${companyName} – ${ticker}` : companyName,
        })
      }

      if (!traces.length) {
        throw new Error(`Nenhuma série retornada para a conta ${accountCode}`)
      }

      return {
        data: traces,
        layout: {
          ...baseLayout,
          title: `${accountCode} – séries por companhia`,
        },
        meta: {
          ...baseMeta,
          account_code: accountCode,
          companies: this.companies,
        },
      }
    },
  },
})
