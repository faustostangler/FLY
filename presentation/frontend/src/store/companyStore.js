import { defineStore } from 'pinia'
// import { COMPANY_FACETS } from '../config/companyFacets'
import { searchCompanies, fetchCompanyFacets } from '../services/apiService'

const DEFAULT_OPERATOR = 'IN'
const SELECTION_SEPARATOR = '::'

const LOGICAL_ALIASES = {
  AND: 'AND',
  MUST: 'AND',
  OR: 'OR',
  SHOULD: 'OR',
  NOT: 'NOT',
  MUST_NOT: 'NOT',
  SHOULD_NOT: 'NOT',
  OR_NOT: 'NOT',
  'OR-NOT': 'NOT',
}

const OPERATOR_ALIASES = {
  IN: 'IN',
  EQUALS: 'EQUALS',
  EQ: 'EQUALS',
  '=': 'EQUALS',
  '==': 'EQUALS',
  CONTAINS: 'CONTAINS',
  HAS: 'CONTAINS',
  STARTS_WITH: 'STARTS_WITH',
  STARTSWITH: 'STARTS_WITH',
  PREFIX: 'STARTS_WITH',
  BETWEEN: 'BETWEEN',
}

const FIELD_ALIASES = {
  sector: 'industry_sector',
  setor: 'industry_sector',
  industry_sector: 'industry_sector',
  subsector: 'industry_subsector',
  subsetor: 'industry_subsector',
  industry_subsector: 'industry_subsector',
  segment: 'industry_segment',
  segmento: 'industry_segment',
  industry_segment: 'industry_segment',
  industry_classification: 'industry_classification',
  classificacao: 'industry_classification',
  industry_classification_eng: 'industry_classification_eng',
  classification_en: 'industry_classification_eng',
  activity: 'activity',
  atividade: 'activity',
  company_segment: 'company_segment',
  segmento_companhia: 'company_segment',
  company_segment_eng: 'company_segment_eng',
  company_category: 'company_category',
  categoria: 'company_category',
  company_type: 'company_type',
  tipo_companhia: 'company_type',
  listing_segment: 'listing_segment',
  segmento_listagem: 'listing_segment',
  registrar: 'registrar',
  escriturador: 'registrar',
  website: 'website',
  site: 'website',
  institution_common: 'institution_common',
  instituicao_ordinaria: 'institution_common',
  institution_preferred: 'institution_preferred',
  instituicao_preferencial: 'institution_preferred',
  market: 'market',
  mercado: 'market',
  market_indicator: 'market_indicator',
  indicador_mercado: 'market_indicator',
  code: 'code',
  codigo: 'code',
  ticker: 'code',
  type_bdr: 'type_bdr',
  tipo_bdr: 'type_bdr',
  reason: 'reason',
  motivo: 'reason',
  company_name: 'company_name',
  companhia: 'company_name',
  company: 'company_name',
  trading_name: 'trading_name',
  trading: 'trading_name',
  nome_pregao: 'trading_name',
  issuing_company: 'issuing_company',
  emissora: 'issuing_company',
  cnpj: 'cnpj',
  has_bdr: 'has_bdr',
  tem_bdr: 'has_bdr',
  has_quotation: 'has_quotation',
  tem_cotacao: 'has_quotation',
  has_emissions: 'has_emissions',
  tem_emissoes: 'has_emissions',
  date_quotation: 'date_quotation',
  data_cotacao: 'date_quotation',
  last_date: 'last_date',
  ultima_data: 'last_date',
  listing_date: 'listing_date',
  data_listagem: 'listing_date',
}

class ParseError extends Error {
  constructor(message) {
    super(message)
    this.name = 'ParseError'
  }
}

function normalizeLogical(value) {
  if (!value) return null
  const key = String(value).toUpperCase()
  return LOGICAL_ALIASES[key] || null
}

function normalizeOperator(value) {
  if (!value) return DEFAULT_OPERATOR
  const key = String(value).toUpperCase()
  return OPERATOR_ALIASES[key] || null
}

function normalizeField(value) {
  if (!value) return null
  const key = String(value).toLowerCase()
  return FIELD_ALIASES[key] || null
}

export function normalizeFacetKey(field) {
  const rawField = String(field || '').trim()
  return normalizeField(rawField) || rawField
}

function normalizeValues(values) {
  return (values || [])
    .map((value) => {
      const raw = String(value ?? '').trim()
      const upper = raw.toUpperCase()
      if (upper === 'TRUE' || upper === 'FALSE') {
        return upper.toLowerCase()
      }
      if (upper === 'SIM') {
        return 'true'
      }
      if (upper === 'NAO' || upper === 'NÃO') {
        return 'false'
      }
      return raw
    })
    .filter((value) => value.length)
}

function cloneClauses(clauses = []) {
  return clauses.map((clause) => ({
    logical: clause.logical,
    condition: clause.condition
      ? {
          field: clause.condition.field,
          operator: clause.condition.operator,
          values: [...(clause.condition.values || [])],
        }
      : undefined,
    group: clause.group
      ? {
          clauses: cloneClauses(clause.group.clauses || []),
        }
      : undefined,
  }))
}

function formatValue(value) {
  const raw = String(value ?? '').trim()
  if (!raw) return ''
  if (/[\s,]/.test(raw)) {
    return `"${raw.replace(/"/g, '\\"')}"`
  }
  return raw
}

function serializeClauses(clauses = []) {
  return clauses
    .map((clause) => {
      const logical = clause.logical || 'AND'
      if (clause.group) {
        const inner = serializeClauses(clause.group.clauses || [])
        return `${logical} (${inner})`
      }
      const condition = clause.condition || {}
      const operator = condition.operator || DEFAULT_OPERATOR
      const values = (condition.values || []).map(formatValue).join(', ')
      return `${logical} ${condition.field} ${operator} (${values})`
    })
    .join(' ; ')
}

function buildSelectionValue(company, ticker) {
  return `${company}${SELECTION_SEPARATOR}${ticker}`
}

function splitSelectionValue(value) {
  if (!value || typeof value !== 'string') {
    return { company: '', ticker: '' }
  }
  const [company, ticker] = value.split(SELECTION_SEPARATOR)
  return { company: company || '', ticker: ticker || '' }
}

// function normalizeBucketValue(value) {
//   const text = String(value ?? '').trim()
//   return text.length ? text : null
// }

// function toArray(value) {
//   if (Array.isArray(value)) return value
//   if (value === null || value === undefined) return []
//   return [value]
// }

// // function buildFacetBuckets(companies = [], fields = []) {
//   const buckets = {}
//   for (const field of fields) {
//     buckets[field] = new Map()
//   }

//   for (const company of companies) {
//     for (const field of fields) {
//       const values = toArray(company?.[field])
//       for (const raw of values) {
//         const value = normalizeBucketValue(raw)
//         if (!value) continue

//         const map = buckets[field]
//         map.set(value, (map.get(value) || 0) + 1)
//       }
//     }
//   }

//   const normalizedBuckets = {}
//   for (const field of fields) {
//     const entries = Array.from(buckets[field].entries()).map(([value, count]) => ({
//       value,
//       count,
//     }))

//     entries.sort((a, b) => {
//       if (b.count !== a.count) return b.count - a.count
//       return a.value.localeCompare(b.value)
//     })

//     normalizedBuckets[field] = entries
//   }

//   return normalizedBuckets
// }

// function bucketsToOptions(buckets = {}) {
//   const options = {}
//   for (const [field, entries] of Object.entries(buckets)) {
//     options[field] = (entries || []).map((entry) => ({
//       value: entry.value,
//       label: entry.value,
//       count: entry.count,
//     }))
//   }
//   return options
// }

function tokenize(input) {
  const tokens = []
  let index = 0
  while (index < input.length) {
    const char = input[index]
    if (/\s/.test(char)) {
      index += 1
      continue
    }
    if (char === '(') {
      tokens.push({ type: 'LPAREN', value: char })
      index += 1
      continue
    }
    if (char === ')') {
      tokens.push({ type: 'RPAREN', value: char })
      index += 1
      continue
    }
    if (char === ',') {
      tokens.push({ type: 'COMMA', value: char })
      index += 1
      continue
    }
    if (char === ';') {
      tokens.push({ type: 'SEMICOLON', value: char })
      index += 1
      continue
    }
    if (char === '"' || char === "'") {
      const quote = char
      index += 1
      let buffer = ''
      let closed = false
      while (index < input.length) {
        const current = input[index]
        if (current === '\\' && index + 1 < input.length) {
          buffer += input[index + 1]
          index += 2
          continue
        }
        if (current === quote) {
          closed = true
          index += 1
          break
        }
        buffer += current
        index += 1
      }
      if (!closed) {
        throw new ParseError('Texto entre aspas não foi fechado.')
      }
      tokens.push({ type: 'STRING', value: buffer })
      continue
    }
    let buffer = ''
    while (index < input.length && !/[\s(),;]/.test(input[index])) {
      buffer += input[index]
      index += 1
    }
    tokens.push({ type: 'WORD', value: buffer })
  }
  return tokens
}

function flattenNode(node, kind) {
  if (!node) return []
  if (node.type === kind) {
    return [...flattenNode(node.left, kind), ...flattenNode(node.right, kind)]
  }
  return [node]
}

function astToClauses(node, parentLogical) {
  if (!node) {
    return []
  }
  if (node.type === 'CLAUSE') {
    return [
      {
        logical: parentLogical,
        condition: {
          field: node.field,
          operator: node.operator,
          values: node.values,
        },
      },
    ]
  }
  if (node.type === 'NOT') {
    const innerClauses = astToClauses(node.operand, 'AND')
    return [
      {
        logical: 'NOT',
        group: { clauses: innerClauses },
      },
    ]
  }
  if (node.type === 'AND' || node.type === 'OR') {
    const nodeLogical = node.type === 'AND' ? 'AND' : 'OR'
    const children = flattenNode(node, node.type)
    const childClauses = children.flatMap((child) => astToClauses(child, nodeLogical))
    if (parentLogical === nodeLogical) {
      return childClauses
    }
    return [
      {
        logical: parentLogical,
        group: { clauses: childClauses },
      },
    ]
  }
  throw new ParseError('Estrutura de consulta inválida.')
}

class QueryParser {
  constructor(tokens) {
    this.tokens = tokens
    this.current = 0
  }

  parse() {
    if (this.tokens.length === 0) {
      return null
    }
    const expression = this.parseExpression()
    if (!this.isAtEnd()) {
      const token = this.peek()
      const value = token?.value || token?.type || 'desconhecido'
      throw new ParseError(`Símbolo inesperado: ${value}`)
    }
    return expression
  }

  parseExpression() {
    let node = this.parseOr()
    while (this.match('SEMICOLON')) {
      if (this.isAtEnd()) {
        break
      }
      const right = this.parseOr()
      if (!right) {
        break
      }
      node = node ? { type: 'AND', left: node, right } : right
    }
    return node
  }

  parseOr() {
    let node = this.parseAnd()
    while (this.matchLogical('OR')) {
      const right = this.parseAnd()
      if (!right) {
        throw new ParseError('Expressão OR incompleta.')
      }
      node = node ? { type: 'OR', left: node, right } : right
    }
    return node
  }

  parseAnd() {
    let node = this.parseUnary()
    while (this.matchLogical('AND')) {
      const right = this.parseUnary()
      if (!right) {
        throw new ParseError('Expressão AND incompleta.')
      }
      node = node ? { type: 'AND', left: node, right } : right
    }
    return node
  }

  parseUnary() {
    if (this.matchLogical('NOT')) {
      const operand = this.parseUnary()
      if (!operand) {
        throw new ParseError('Esperado expressão após NOT.')
      }
      return { type: 'NOT', operand }
    }
    if (this.match('LPAREN')) {
      const expression = this.parseExpression()
      this.consume('RPAREN', 'Esperado ) para fechar o grupo.')
      return expression
    }
    return this.parseClause()
  }

  parseClause() {
    while (true) {
      const token = this.peek()
      if (!token || token.type !== 'WORD') {
        break
      }
      const logical = normalizeLogical(token.value)
      if (logical && logical !== 'NOT') {
        this.advance()
        continue
      }
      break
    }

    const fieldToken = this.consumeWord('Informe o campo da companhia.')
    const field = normalizeField(fieldToken.value)
    if (!field) {
      throw new ParseError(`Campo desconhecido: ${fieldToken.value}`)
    }

    const operatorToken = this.consumeWord('Informe o operador de comparação.')
    const operator = normalizeOperator(operatorToken.value)
    if (!operator) {
      throw new ParseError(`Operador inválido: ${operatorToken.value}`)
    }

    this.consume('LPAREN', 'Esperado ( para iniciar a lista de valores.')
    const values = []
    if (this.check('RPAREN')) {
      this.advance()
    } else {
      while (!this.isAtEnd()) {
        if (this.check('RPAREN')) {
          this.advance()
          break
        }
        const value = this.consumeValue()
        values.push(value)
        if (this.check('RPAREN')) {
          this.advance()
          break
        }
        this.consume('COMMA', 'Separar valores com vírgula.')
      }
    }

    const normalizedValues = normalizeValues(values)
    if (!normalizedValues.length && !['CONTAINS', 'STARTS_WITH'].includes(operator)) {
      throw new ParseError(`Informe pelo menos um valor para ${field}.`)
    }

    if (operator === 'BETWEEN' && normalizedValues.length !== 2) {
      throw new ParseError(`O operador BETWEEN exige dois valores para ${field}.`)
    }

    return {
      type: 'CLAUSE',
      field,
      operator,
      values: normalizedValues,
    }
  }

  match(type) {
    if (!this.check(type)) {
      return false
    }
    this.advance()
    return true
  }

  matchLogical(expected) {
    const token = this.peek()
    if (!token || token.type !== 'WORD') {
      return false
    }
    const logical = normalizeLogical(token.value)
    if (logical !== expected) {
      return false
    }
    this.advance()
    return true
  }

  consume(type, message) {
    if (this.check(type)) {
      return this.advance()
    }
    throw new ParseError(message)
  }

  consumeWord(message) {
    const token = this.peek()
    if (!token || token.type !== 'WORD') {
      throw new ParseError(message)
    }
    this.advance()
    return token
  }

  consumeValue() {
    const token = this.peek()
    if (!token) {
      throw new ParseError('Valor ausente na lista.')
    }
    if (token.type === 'STRING') {
      this.advance()
      return token.value
    }
    if (token.type === 'WORD') {
      const parts = [this.advance().value]
      while (!this.isAtEnd()) {
        const next = this.peek()
        if (!next || next.type !== 'WORD') {
          break
        }
        parts.push(this.advance().value)
      }
      return parts.join(' ')
    }
    throw new ParseError('Valor inválido na lista.')
  }

  check(type) {
    if (this.isAtEnd()) {
      return false
    }
    return this.peek().type === type
  }

  advance() {
    if (!this.isAtEnd()) {
      this.current += 1
    }
    return this.previous()
  }

  peek() {
    return this.tokens[this.current]
  }

  previous() {
    return this.tokens[this.current - 1]
  }

  isAtEnd() {
    return this.current >= this.tokens.length
  }
}

function parseTextToQuery(text) {
  try {
    const tokens = tokenize(text)
    const parser = new QueryParser(tokens)
    const ast = parser.parse()
    if (!ast) {
      return { clauses: [] }
    }
    const clauses = astToClauses(ast, 'AND')
    return { clauses }
  } catch (error) {
    if (error instanceof ParseError) {
      throw error
    }
    throw new ParseError('Não foi possível interpretar a consulta fornecida.')
  }
}

export const useCompanyStore = defineStore('companyStore', {
  state: () => ({
    // Filtro efetivo usado pela API e pelos charts (combinação)
    filterQuery: { clauses: [] },

    // Filtro universal das facetas (chips “X”)
    facetQuery: { clauses: [] },

    // Filtro do query builder (texto + “enviar para consulta”)
    builderQuery: { clauses: [] },

    // Texto do query builder
    queryText: '',

    // Lista bruta vinda da API (normalizada em loadCompanies)
    companies: [],
    // Lista que pode ser filtrada por preview (live filter)
    filteredCompanies: [],
    total: 0,
    facets: {},
    selectedItems: [],
    isLoading: false,
    error: null,

    // Estrutura da cascata Setor → Subsetor → Segmento
    industryCascade: {
      sectorToSubsectors: {},
      sectorToSegments: {},
      subsectorToSegments: {},
    },

      previewFilters: {},
  }),

  getters: {
    clauseByField(state) {
      const map = {}
      for (const clause of state.filterQuery.clauses || []) {
        if (clause.condition && clause.condition.field) {
          map[clause.condition.field] = clause
        }
      }
      return map
    },
    selectedPairs(state) {
      return (state.selectedItems || []).map(splitSelectionValue)
    },

    previewedCompanies(state) {
      const filters = state.previewFilters || {}
      const companies = state.companies || []

      const entries = Object.entries(filters)
        .map(([field, values]) => [
          field,
          (values || []).map((v) => String(v || '').trim()).filter(Boolean),
        ])
        .filter(([, values]) => values.length)

      if (!entries.length) {
        return companies
      }

      return companies.filter((company) =>
        entries.every(([field, values]) => {
          const raw = company[field]
          if (raw == null) return false
          const normalizedValues = toArray(raw)
            .map((value) => String(value || '').trim())
            .filter(Boolean)

          if (!normalizedValues.length) return false
          return values.some((value) => normalizedValues.includes(value))
        }),
      )
    },

    // dynamicFacetBuckets() {
    //   const facetFields = COMPANY_FACETS.map((facet) => facet.field)

    //   const hasPreview =
    //     this.previewFilters && Object.keys(this.previewFilters).length > 0

    //   const baseCompanies = hasPreview ? this.previewedCompanies : this.companies

    //   return buildFacetBuckets(baseCompanies, facetFields)
    // },

    // dynamicFacetOptions() {
    //   const buckets = this.dynamicFacetBuckets
    //   return bucketsToOptions(buckets)
    // },

    selectedValuesByField(state) {
      const result = {}
      for (const clause of state.facetQuery.clauses || []) {
        const condition = clause.condition || {}
        const field = condition.field
        const values = condition.values || []

        if (!field || !values.length) continue
        result[field] = [...values]
      }
      return result
    },
  },

  actions: {
    _updateFilterQuery() {
      const facetClauses = Array.isArray(this.facetQuery?.clauses)
        ? this.facetQuery.clauses
        : []
      const builderClauses = Array.isArray(this.builderQuery?.clauses)
        ? this.builderQuery.clauses
        : []

      this.filterQuery = {
        clauses: [...facetClauses, ...builderClauses],
      }
    },

    setPreviewFacet(field, values) {
      const normalizedField = String(field || '').trim()
      const normalizedValues = Array.isArray(values)
        ? values.map((v) => String(v || '').trim()).filter(Boolean)
        : []

      if (!normalizedField) {
        return
      }

      if (!normalizedValues.length) {
        this.clearPreviewFacet(normalizedField)
        return
      }

      this.previewFilters = {
        ...this.previewFilters,
        [normalizedField]: normalizedValues,
      }

      this._applyPreviewFilters()
    },

    clearPreviewFacet(field) {
      const normalizedField = String(field || '').trim()
      if (!normalizedField) {
        return
      }
      const next = { ...this.previewFilters }
      delete next[normalizedField]
      this.previewFilters = next
      this._applyPreviewFilters()
    },

    clearAllPreviewFilters() {
      this.previewFilters = {}
      this._applyPreviewFilters()
    },

    // Filtro universal (facetas + chips “X”)
    setFacetFilter(field, logical, values, operator = DEFAULT_OPERATOR) {
      const normalizedField = normalizeField(field) || field
      const normalizedValues = normalizeValues(values)
      const normalizedOperator = normalizeOperator(operator) || DEFAULT_OPERATOR

      if (!normalizedField) return

      const normalizedLogical = normalizeLogical(logical) || 'AND'
      const clauses = cloneClauses(this.facetQuery.clauses || [])
      const filteredClauses = clauses.filter(
        (clause) => !clause.condition || clause.condition.field !== normalizedField,
      )

      if (normalizedValues.length) {
        filteredClauses.push({
          logical: normalizedLogical,
          condition: {
            field: normalizedField,
            operator: normalizedOperator,
            values: normalizedValues,
          },
        })
      }

      this.facetQuery = { clauses: filteredClauses }
      this._updateFilterQuery()
    },

    // Wrapper para compatibilidade com chamadas antigas
    setFacetSelection(field, logical, values, operator = DEFAULT_OPERATOR) {
      this.setFacetFilter(field, logical, values, operator)
    },

    // Query builder: cláusulas geradas via “Enviar para consulta”
    setBuilderFacet(field, logical, values, operator = DEFAULT_OPERATOR) {
      const normalizedField = normalizeField(field) || field
      const normalizedValues = normalizeValues(values)
      const normalizedOperator = normalizeOperator(operator) || DEFAULT_OPERATOR
      const normalizedLogical = normalizeLogical(logical) || 'AND'

      if (!normalizedField) return

      const clauses = cloneClauses(this.builderQuery.clauses || [])
      const filteredClauses = clauses.filter(
        (clause) => !clause.condition || clause.condition.field !== normalizedField,
      )

      if (normalizedValues.length) {
        filteredClauses.push({
          logical: normalizedLogical,
          condition: {
            field: normalizedField,
            operator: normalizedOperator,
            values: normalizedValues,
          },
        })
      }

      this.builderQuery = { clauses: filteredClauses }
      this._updateFilterQuery()
      this.queryText = this.serializeQuery(this.builderQuery)

      // espelho em selection/logical/operators com base no filtro combinado
      this._syncSelectionFromFilterQuery(this.filterQuery)
    },

    // Chips tiram valores só do filtro universal
    removeFacetValue(field, value) {
      const key = normalizeFacetKey(field)
      if (!key) return

      const current = this.selectedValuesByField[key] || []
      const normalizedTarget = normalizeValues([value])[0]
      const nextValues = current.filter((item) => item !== normalizedTarget)

      this.setFacetFilter(key, 'AND', nextValues, DEFAULT_OPERATOR)
    },

    setQueryText(text) {
      this.queryText = text
    },

    applyQueryText() {
      try {
        const parsed = this.parseQuery(this.queryText)

        // texto controla só o builderQuery
        this.builderQuery = parsed
        this._updateFilterQuery()
        this.queryText = this.serializeQuery(this.builderQuery)

        // espelho em selection/logical/operators com base no filtro combinado
        this._syncSelectionFromFilterQuery(this.filterQuery)

        this.previewFilters = {}
        this.loadCompanies()
        return { ok: true }
      } catch (error) {
        const message = error instanceof ParseError ? error.message : 'Consulta inválida.'
        return { ok: false, message }
      }
    },

    resetFilters() {
      this.facetQuery = { clauses: [] }
      this.builderQuery = { clauses: [] }
      this.filterQuery = { clauses: [] }
      this.queryText = ''
      this.selectedItems = []
      this.selection = {}
      this.logical = {}
      this.operators = {}
      this.previewFilters = {}
      this.loadCompanies()
    },

    setSelectedItems(values) {
      const normalized = Array.isArray(values)
        ? values.map((value) => String(value)).filter((value) => value.length)
        : []
      this.selectedItems = normalized
    },

    async loadCompanies() {
      this.isLoading = true
      this.error = null
      try {
        const payload = await searchCompanies(this.filterQuery)
        const rawItems = payload.items || []

        this.companies = rawItems.map((item) => ({
          ...item,
          // normaliza nomes de campos para bater com COMPANY_FACETS
          industry_sector: item.industry_sector || item.sector || '',
          industry_subsector: item.industry_subsector || item.subsector || '',
          industry_segment: item.industry_segment || item.segment || '',
          issuing_company: item.issuing_company || '',
          code: item.code || (Array.isArray(item.tickers) ? item.tickers[0] : ''),
          cnpj: item.cnpj || '',
        }))
        this.total = payload.total || 0

        // reseta preview e lista filtrada
        this.previewFilters = {}
        this.filteredCompanies = this.companies

        // reconstrói o grafo da cascata Setor → Subsetor → Segmento
        this._rebuildIndustryCascade(this.companies)

        // garante que seleção de empresas continua válida
        this._pruneSelection()
        // aqui NÃO mexe em queryText
      } catch (err) {
        console.error(err)
        this.error = 'Falha ao carregar companhias'
      } finally {
        this.isLoading = false
      }

    },

    async loadFacets() {
      try {
        const payload = await fetchCompanyFacets()
        this.facets = payload.facets || {}
      } catch (err) {
        console.error(err)
      }
    },

    serializeQuery(query) {
      if (!query || !Array.isArray(query.clauses) || query.clauses.length === 0) {
        return ''
      }
      return serializeClauses(query.clauses)
    },

    parseQuery(text) {
      if (!text || !text.trim()) {
        return { clauses: [] }
      }
      return parseTextToQuery(text)
    },

    _syncSelectionFromFilterQuery(query = this.filterQuery) {
      const clauses = Array.isArray(query?.clauses) ? query.clauses : []

      const nextSelection = {}
      const nextLogical = {}
      const nextOperators = {}

      for (const clause of clauses) {
        const condition = clause?.condition || {}
        const field = condition.field ? normalizeField(condition.field) || condition.field : null
        const values = normalizeValues(condition.values || [])
        if (!field || !values.length) continue

        nextSelection[field] = values
        nextLogical[field] = normalizeLogical(clause.logical) || 'AND'
        nextOperators[field] = normalizeOperator(condition.operator) || DEFAULT_OPERATOR
      }

      this.selection = nextSelection
      this.logical = nextLogical
      this.operators = nextOperators
    },

    _rebuildIndustryCascade(items = []) {
      const sectorToSubsectors = new Map()
      const sectorToSegments = new Map()
      const subsectorToSegments = new Map()

      for (const company of items || []) {
        const sector = (company.industry_sector || company.sector || '').trim()
        const subsector = (company.industry_subsector || company.subsector || '').trim()
        const segment = (company.industry_segment || company.segment || '').trim()

        if (!sector && !subsector && !segment) continue

        if (sector) {
          if (!sectorToSubsectors.has(sector)) {
            sectorToSubsectors.set(sector, new Set())
          }
          if (!sectorToSegments.has(sector)) {
            sectorToSegments.set(sector, new Set())
          }
        }

        if (subsector) {
          if (!subsectorToSegments.has(subsector)) {
            subsectorToSegments.set(subsector, new Set())
          }
        }

        if (sector && subsector) {
          sectorToSubsectors.get(sector).add(subsector)
        }

        if (sector && segment) {
          sectorToSegments.get(sector).add(segment)
        }

        if (subsector && segment) {
          subsectorToSegments.get(subsector).add(segment)
        }
      }

      const normalizeMap = (map) => {
        const result = {}
        for (const [key, set] of map.entries()) {
          const values = Array.from(set).filter((value) => value && value.length)
          if (values.length) {
            result[key] = values.sort((a, b) => a.localeCompare(b, 'pt-BR'))
          }
        }
        return result
      }

      this.industryCascade = {
        sectorToSubsectors: normalizeMap(sectorToSubsectors),
        sectorToSegments: normalizeMap(sectorToSegments),
        subsectorToSegments: normalizeMap(subsectorToSegments),
      }
    },

    _pruneSelection() {
      if (!this.selectedItems || this.selectedItems.length === 0) {
        return
      }
      const valid = new Set()
      for (const company of this.filteredCompanies || this.companies || []) {
        const companyName = company.company_name || ''
        for (const ticker of company.tickers || []) {
          if (!ticker) continue
          valid.add(buildSelectionValue(companyName, ticker))
        }
      }
      const filtered = this.selectedItems.filter((value) => valid.has(value))
      if (filtered.length !== this.selectedItems.length) {
        this.selectedItems = filtered
      }
    },

    _applyPreviewFilters() {
      this.filteredCompanies = this.previewedCompanies
      this._pruneSelection()
    },
  },
})

export { ParseError }
