import { defineStore } from 'pinia'
import { fetchAccountLineChart } from '../services/apiService'

export const useAccountChartsStore = defineStore('accountCharts', {
  state: () => ({
    ticker: '',
    charts: {
      '02.03': null,
      '03.01': null,
    },
    isLoading: {
      '02.03': false,
      '03.01': false,
    },
    error: {
      '02.03': '',
      '03.01': '',
    },
  }),
  actions: {
    setTicker(ticker) {
      this.ticker = String(ticker || '').trim()
    },

    _ensureKeys(code) {
      if (!(code in this.charts)) {
        this.charts = { ...this.charts, [code]: null }
      }
      if (!(code in this.isLoading)) {
        this.isLoading = { ...this.isLoading, [code]: false }
      }
      if (!(code in this.error)) {
        this.error = { ...this.error, [code]: '' }
      }
    },

    async loadAccountChart(accountCode, params = {}) {
      const code = String(accountCode || '').trim()
      if (!code) {
        return
      }

      this._ensureKeys(code)

      if (!this.ticker) {
        this.error = {
          ...this.error,
          [code]: 'Ticker e código da conta são obrigatórios',
        }
        return
      }

      this.isLoading = { ...this.isLoading, [code]: true }
      this.error = { ...this.error, [code]: '' }

      try {
        const chart = await fetchAccountLineChart(this.ticker, code, params)
        this.charts = { ...this.charts, [code]: chart }
      } catch (err) {
        console.error(err)
        const message = err?.message || 'Falha ao carregar gráfico'
        this.error = { ...this.error, [code]: message }
        this.charts = { ...this.charts, [code]: null }
      } finally {
        this.isLoading = { ...this.isLoading, [code]: false }
      }
    },

    async loadMultipleAccounts(accountCodes, params = {}) {
      const codes = (accountCodes || [])
        .map(code => String(code || '').trim())
        .filter(Boolean)

      await Promise.all(codes.map(code => this.loadAccountChart(code, params)))
    },
  },
})
