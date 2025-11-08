import { defineStore } from 'pinia'

const DEFAULT_FACET_CONFIGS = [
  {
    field: 'sector',
    label: 'Setor',
    multiple: true,
  },
  {
    field: 'segment',
    label: 'Segmento',
    multiple: true,
  },
]

const DEFAULT_FACET_OPTIONS = {
  sector: [
    { value: 'Energia', label: 'Energia' },
    { value: 'Financeiro', label: 'Financeiro' },
    { value: 'Tecnologia', label: 'Tecnologia' },
  ],
  segment: [
    { value: 'Distribuição', label: 'Distribuição' },
    { value: 'Serviços', label: 'Serviços' },
  ],
}

function createCompanyDataset() {
  return [
    {
      company_name: 'Fly Energia',
      trading_name: 'Fly Energia Participações',
      sector: 'Energia',
      subsector: 'Energia Elétrica',
      segment: 'Distribuição',
      tickers: ['FLY3'],
      market: 'B3',
    },
    {
      company_name: 'Banco Fly',
      trading_name: 'Banco Fly S.A.',
      sector: 'Financeiro',
      subsector: 'Bancos',
      segment: 'Serviços Financeiros',
      tickers: ['FLYB11'],
      market: 'B3',
    },
    {
      company_name: 'Petróleo do Brasil',
      trading_name: 'Petrobras',
      sector: 'Energia',
      subsector: 'Petróleo, Gás e Biocombustíveis',
      segment: 'Exploração e Produção',
      tickers: ['PETR4'],
      market: 'B3',
    },
  ]
}

function parseSelectionValue(value) {
  if (!value) return { companyName: '', ticker: '' }
  const [companyName = '', ticker = ''] = String(value).split('::')
  return { companyName, ticker }
}

export const useCompanyStore = defineStore('companyStore', {
  state: () => ({
    facetConfigs: DEFAULT_FACET_CONFIGS,
    facetOptionsIndex: DEFAULT_FACET_OPTIONS,
    clauseLogicalIndex: {},
    clauseValuesIndex: {},
    queryText: '',
    parseError: '',
    companies: [],
    selectedItems: [],
    selectedTicker: '',
    total: 0,
    error: '',
    isLoading: false,
  }),

  getters: {
    facets(state) {
      return state.facetConfigs
    },
    facetOptions: (state) => (field) => state.facetOptionsIndex[field] || [],
    clauseValues: (state) => (field) => state.clauseValuesIndex[field] || [],
    clauseLogical: (state) => (field) => state.clauseLogicalIndex[field] || 'AND',
    selectedSummaries(state) {
      const index = new Map()
      for (const company of state.companies) {
        const companyName = company.company_name || ''
        for (const ticker of company.tickers || []) {
          if (!ticker) continue
          const key = `${companyName}::${ticker}`
          index.set(key, {
            key,
            companyName,
            ticker,
            tradingName: company.trading_name || '',
            sector: company.sector || '',
            subsector: company.subsector || '',
            segment: company.segment || '',
            market: company.market || '',
          })
        }
      }

      return state.selectedItems
        .map((value) => index.get(value))
        .filter(Boolean)
    },
  },

  actions: {
    loadCompanies() {
      this.isLoading = true
      this.error = ''

      setTimeout(() => {
        const companies = createCompanyDataset()
        this.companies = companies
        this.total = companies.length
        this.isLoading = false

        if (this.selectedTicker) {
          this.setSelectedTicker(this.selectedTicker)
        }
      }, 200)
    },

    reload() {
      this.loadCompanies()
    },

    clearFilters() {
      this.clauseLogicalIndex = {}
      this.clauseValuesIndex = {}
      this.queryText = ''
      this.parseError = ''
      this.selectedItems = []
      this.selectedTicker = ''
      this.companies = []
      this.total = 0
    },

    applyQuery() {
      if (this.queryText && !this.queryText.trim().toUpperCase().startsWith('AND')) {
        this.parseError = 'Consulta deve iniciar com AND'
        return
      }
      this.parseError = ''
    },

    updateQueryText(value) {
      this.queryText = value
    },

    updateSelectedItems(values) {
      this.selectedItems = Array.isArray(values)
        ? values.map((value) => String(value)).filter((value) => value.length)
        : []

      if (!this.selectedTicker) {
        this.syncSelectedTickerFromSelection()
      }
    },

    updateFacet({ field, value }) {
      if (!field) return
      const normalizedField = String(field)
      const current = new Set(this.clauseValuesIndex[normalizedField] || [])
      if (current.has(value)) {
        current.delete(value)
      } else {
        current.add(value)
      }
      this.clauseValuesIndex = {
        ...this.clauseValuesIndex,
        [normalizedField]: Array.from(current),
      }
    },

    setSelectedTicker(ticker) {
      const normalized = ticker ? String(ticker) : ''
      if (this.selectedTicker !== normalized) {
        this.selectedTicker = normalized
      }

      if (!normalized) {
        return
      }

      const existsInSelection = this.selectedSummaries.some(
        (summary) => summary.ticker === normalized,
      )
      if (existsInSelection) {
        return
      }

      // ensure ticker is represented in selection when available
      const matches = this.companies
        .flatMap((company) =>
          (company.tickers || []).map((tickerValue) => ({ company, tickerValue })),
        )
        .filter((entry) => entry.tickerValue === normalized)
        .map(({ company, tickerValue }) => `${company.company_name || ''}::${tickerValue}`)

      if (matches.length) {
        const values = new Set(this.selectedItems)
        matches.forEach((match) => values.add(match))
        this.selectedItems = Array.from(values)
      }
    },

    syncSelectedTickerFromSelection() {
      if (this.selectedTicker) {
        return
      }
      const [first] = this.selectedItems
      if (!first) {
        return
      }
      const { ticker } = parseSelectionValue(first)
      this.selectedTicker = ticker
    },
  },
})

export function seedCompanies(store) {
  const companies = createCompanyDataset()
  if (store) {
    store.companies = companies
    store.total = companies.length
    store.selectedItems = companies
      .flatMap((company) => (company.tickers || []).map((ticker) => `${company.company_name}::${ticker}`))
  }
}
