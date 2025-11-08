import { defineStore } from 'pinia'

const DEFAULT_TICKER = 'PETR4'

const MOCK_CHART_DATA = {
  PETR4: {
    title: 'PETR4 · Histórico de preços',
    series: [
      { date: '2024-05-06', close: 38.21 },
      { date: '2024-05-07', close: 37.94 },
      { date: '2024-05-08', close: 38.7 },
      { date: '2024-05-09', close: 39.12 },
      { date: '2024-05-10', close: 39.56 },
    ],
  },
  FLY3: {
    title: 'FLY3 · Histórico de preços',
    series: [
      { date: '2024-05-06', close: 12.35 },
      { date: '2024-05-07', close: 12.5 },
      { date: '2024-05-08', close: 12.82 },
      { date: '2024-05-09', close: 12.3 },
      { date: '2024-05-10', close: 12.55 },
    ],
  },
  FLYB11: {
    title: 'FLYB11 · Histórico de preços',
    series: [
      { date: '2024-05-06', close: 24.12 },
      { date: '2024-05-07', close: 24.4 },
      { date: '2024-05-08', close: 24.78 },
      { date: '2024-05-09', close: 24.33 },
      { date: '2024-05-10', close: 24.61 },
    ],
  },
}

function buildChartPayload(ticker) {
  const normalized = ticker && MOCK_CHART_DATA[ticker]
  if (normalized) {
    return normalized
  }

  return {
    title: `${ticker || DEFAULT_TICKER} · Histórico de preços`,
    series: [
      { date: '2024-05-06', close: 20.0 },
      { date: '2024-05-07', close: 20.1 },
      { date: '2024-05-08', close: 20.4 },
      { date: '2024-05-09', close: 20.25 },
      { date: '2024-05-10', close: 20.45 },
    ],
  }
}

export const useChartStore = defineStore('chartStore', {
  state: () => ({
    params: {
      type: DEFAULT_TICKER,
    },
    chart: null,
    isLoading: false,
    error: '',
    lastLoadedTicker: '',
  }),

  actions: {
    setType(type) {
      this.params.type = type || DEFAULT_TICKER
    },

    async loadChartByTicker(ticker) {
      const normalized = ticker ? String(ticker).toUpperCase() : ''
      const target = normalized || this.params.type || DEFAULT_TICKER
      if (target !== this.params.type) {
        this.setType(target)
      }

      if (this.isLoading && this.params.type === target) {
        return
      }

      if (this.lastLoadedTicker === target && this.chart && !this.error) {
        return
      }

      await this.loadChart()
    },

    async loadChart() {
      const ticker = this.params.type || DEFAULT_TICKER
      this.isLoading = true
      this.error = ''

      await new Promise((resolve) => setTimeout(resolve, 150))

      try {
        this.chart = buildChartPayload(ticker)
        this.lastLoadedTicker = ticker
      } catch (error) {
        console.error(error)
        this.chart = null
        this.error = 'Falha ao carregar gráfico'
        this.lastLoadedTicker = ''
      } finally {
        this.isLoading = false
      }
    },
  },
})
