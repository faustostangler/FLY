import { defineStore } from 'pinia'
import { searchCompanies } from '../services/apiService'

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
}

const FIELD_ALIASES = {
  sector: 'sector',
  setor: 'sector',
  subsector: 'subsector',
  subsetor: 'subsector',
  segment: 'segment',
  segmento: 'segment',
  company_name: 'company_name',
  companhia: 'company_name',
  company: 'company_name',
  trading_name: 'trading_name',
  trading: 'trading_name',
  nome_pregao: 'trading_name',
  ticker: 'ticker',
  codigo: 'ticker',
  code: 'ticker',
  institution_preferred: 'institution_preferred',
  instituicao_preferencial: 'institution_preferred',
  institution_common: 'institution_common',
  instituicao_ordinaria: 'institution_common',
  market: 'market',
  mercado: 'market',
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

function normalizeValues(values) {
  return (values || [])
    .map((value) => String(value ?? '').trim())
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
    filterQuery: { clauses: [] },
    queryText: '',
    companies: [],
    total: 0,
    facets: {},
    selectedItems: [],
    selectedTicker: '',
    isLoading: false,
    error: null,
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
  },

  actions: {
    setFacetSelection(field, logical, values, operator = DEFAULT_OPERATOR) {
      const normalizedField = normalizeField(field) || field
      const normalizedLogical = normalizeLogical(logical) || 'AND'
      const normalizedValues = normalizeValues(values)
      const normalizedOperator = normalizeOperator(operator) || DEFAULT_OPERATOR

      const clauses = cloneClauses(this.filterQuery.clauses || [])
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

      this.filterQuery = { clauses: filteredClauses }
      this.queryText = this.serializeQuery(this.filterQuery)
      this.loadCompanies()
    },

    setQueryText(text) {
      this.queryText = text
    },

    applyQueryText() {
      try {
        const parsed = this.parseQuery(this.queryText)
        this.filterQuery = parsed
        this.queryText = this.serializeQuery(parsed)
        this.loadCompanies()
        return { ok: true }
      } catch (error) {
        const message = error instanceof ParseError ? error.message : 'Consulta inválida.'
        return { ok: false, message }
      }
    },

    resetFilters() {
      this.filterQuery = { clauses: [] }
      this.queryText = ''
      this.selectedItems = []
      this.selectedTicker = ''
      this.loadCompanies()
    },

    setSelectedItems(values) {
      const normalized = Array.isArray(values)
        ? values.map((value) => String(value)).filter((value) => value.length)
        : []
      this.selectedItems = normalized
    },

    setSelectedTicker(ticker) {
      this.selectedTicker = ticker ? String(ticker) : ''
    },

    async loadCompanies() {
      this.isLoading = true
      this.error = null
      try {
        const payload = await searchCompanies(this.filterQuery)
        this.companies = payload.items || []
        this.total = payload.total || 0
        this.facets = payload.facets || {}
        this._pruneSelection()
        if (!this.queryText) {
          this.queryText = this.serializeQuery(this.filterQuery)
        }
      } catch (err) {
        console.error(err)
        this.error = 'Falha ao carregar companhias'
      } finally {
        this.isLoading = false
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

    _pruneSelection() {
      if (!this.selectedItems || this.selectedItems.length === 0) {
        return
      }
      const valid = new Set()
      for (const company of this.companies || []) {
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
  },
})

export { ParseError }
