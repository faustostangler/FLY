import { reactive, computed } from 'vue'

const state = reactive({
  facetConfigs: [
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
  ],
  facets: new Map(),
  facetOptions: new Map([
    [
      'sector',
      [
        { value: 'Energia', label: 'Energia' },
        { value: 'Financeiro', label: 'Financeiro' },
        { value: 'Tecnologia', label: 'Tecnologia' },
      ],
    ],
    [
      'segment',
      [
        { value: 'Distribuição', label: 'Distribuição' },
        { value: 'Serviços', label: 'Serviços' },
      ],
    ],
  ]),
  clauseLogical: new Map(),
  clauseValues: new Map(),
  queryText: '',
  parseError: '',
  companies: [],
  selectedItems: [],
  total: 0,
  error: '',
  isLoading: false,
})

function companyKey(company) {
  const name = company.company_name || ''
  const ticker = company.tickers?.[0] || ''
  return `${name}::${ticker}`
}

export function useCompanyStore() {
  const computedFacetOptions = (field) => state.facetOptions.get(field) || []
  const computedClauseValues = (field) => state.clauseValues.get(field) || []
  const computedClauseLogical = (field) => state.clauseLogical.get(field) || 'AND'

  const reload = () => {
    state.isLoading = true
    setTimeout(() => {
      const companies = [
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
      ]
      state.companies = companies
      state.total = companies.length
      state.error = ''
      state.isLoading = false
    }, 300)
  }

  const clearFilters = () => {
    state.facets.clear()
    state.clauseValues.clear()
    state.clauseLogical.clear()
    state.queryText = ''
    state.parseError = ''
    state.selectedItems = []
    state.companies = []
    state.total = 0
  }

  const applyQuery = () => {
    if (state.queryText && !state.queryText.trim().startsWith('AND')) {
      state.parseError = 'Consulta deve iniciar com AND'
      return
    }
    state.parseError = ''
  }

  const updateQueryText = (value) => {
    state.queryText = value
  }

  const updateSelectedItems = (value) => {
    state.selectedItems = Array.isArray(value) ? value : []
  }

  const updateFacet = ({ field, value }) => {
    const current = new Set(state.clauseValues.get(field) || [])
    if (current.has(value)) {
      current.delete(value)
    } else {
      current.add(value)
    }
    state.clauseValues.set(field, Array.from(current))
  }

  const selectedItems = computed(() => state.selectedItems)

  const companies = computed(() => state.companies)

  return {
    get facetConfigs() {
      return state.facetConfigs
    },
    get companies() {
      return companies.value
    },
    get total() {
      return state.total
    },
    get error() {
      return state.error
    },
    get isLoading() {
      return state.isLoading
    },
    get parseError() {
      return state.parseError
    },
    get queryText() {
      return state.queryText
    },
    get selectedItems() {
      return selectedItems.value
    },
    facetOptions: computedFacetOptions,
    clauseValues: computedClauseValues,
    clauseLogical: computedClauseLogical,
    reload,
    clearFilters,
    applyQuery,
    updateQueryText,
    updateSelectedItems,
    updateFacet,
  }
}

export function seedCompanies() {
  state.companies = [
    {
      company_name: 'Fly Energia',
      trading_name: 'Fly Energia Participações',
      sector: 'Energia',
      subsector: 'Energia Elétrica',
      segment: 'Distribuição',
      tickers: ['FLY3'],
      market: 'B3',
    },
  ]
  state.selectedItems = state.companies.map((company) => companyKey(company))
  state.total = state.companies.length
}
