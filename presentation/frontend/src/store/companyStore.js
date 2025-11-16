import { defineStore } from 'pinia'
import {
  searchCompanies,
  fetchCompanyFacets,
  fetchCompanyFacetsForQuery,
} from '../services/apiService'

/**
 * Default comparison operator when the user does not explicitly provide one.
 * Example: "sector (Financial)" implicitly becomes "sector IN (Financial)".
 */
const DEFAULT_OPERATOR = 'IN'

/**
 * Separator between company name and ticker in the selection list.
 * Example: "PETROBRAS::PETR4"
 */
const SELECTION_SEPARATOR = '::'

/**
 * Map of aliases for logical operators.
 * The goal is to accept variations (MUST, SHOULD, etc.) and normalize them
 * into a small set of stable values.
 */
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

/**
 * Map of aliases for comparison operators.
 * Keeps the internal API stable while allowing the user to write operators
 * in several different ways.
 */
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

/**
 * Map of aliases for company-domain field names.
 * The purpose is to decouple the textual interface from the real names used
 * in the API/back-end.
 */
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

/**
 * Specific error type for parsing problems in the search language.
 * Keeps syntax errors separate from generic JavaScript errors.
 */
class ParseError extends Error {
  constructor(message) {
    super(message)
    this.name = 'ParseError'
  }
}

/**
 * Normalizes any value to a stable logical operator (AND/OR/NOT).
 *
 * @param {string} value - textual value provided by the user (AND, must, etc.)
 * @returns {'AND'|'OR'|'NOT'|null}
 */
function normalizeLogical(value) {
  if (!value) return null
  const key = String(value).toUpperCase()
  return LOGICAL_ALIASES[key] || null
}

/**
 * Normalizes any value to a stable comparison operator.
 *
 * @param {string} value
 * @returns {string} normalized operator (IN, EQUALS, CONTAINS, etc.)
 */
function normalizeOperator(value) {
  if (!value) return DEFAULT_OPERATOR
  const key = String(value).toUpperCase()
  return OPERATOR_ALIASES[key] || null
}

/**
 * Normalizes a field name to the internal canonical identifier.
 *
 * @param {string} value
 * @returns {string|null} canonical field name, or null if unknown
 */
function normalizeField(value) {
  if (!value) return null
  const key = String(value).toLowerCase()
  return FIELD_ALIASES[key] || null
}

/**
 * Normalizes a list of values:
 * - converts "TRUE"/"FALSE"/"SIM"/"NÃO" to "true"/"false"
 * - trims whitespace
 * - removes empty values
 */
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

/**
 * Creates a deep, immutable copy of the clause list.
 * This prevents subtle bugs caused by shared references between calls.
 */
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

/**
 * Formats a single value to be serialized in the textual language:
 * - adds quotes if it contains spaces or commas
 * - escapes internal quotes
 */
function formatValue(value) {
  const raw = String(value ?? '').trim()
  if (!raw) return ''
  if (/[\s,]/.test(raw)) {
    return `"${raw.replace(/"/g, '\\"')}"`
  }
  return raw
}

/**
 * Serializes a list of normalized clauses into a query string.
 * Example:
 *   [{ logical:'AND', condition:{ field:'sector', operator:'IN', values:['Financial'] }}]
 * becomes:
 *   "AND sector IN (Financial)"
 */
function serializeClauses(clauses = []) {
  return clauses
    .map((clause) => {
      const logical = clause.logical || 'AND'
      if (clause.group) {
        // Logical group with parentheses
        const inner = serializeClauses(clause.group.clauses || [])
        return `${logical} (${inner})`
      }
      // Simple clause: field-operator-values
      const condition = clause.condition || {}
      const operator = condition.operator || DEFAULT_OPERATOR
      const values = (condition.values || []).map(formatValue).join(', ')
      return `${logical} ${condition.field} ${operator} (${values})`
    })
    .join(' ; ')
}

/**
 * Builds the selection value "Company::TICKER".
 * This is the format stored in the selectedItems state.
 */
function buildSelectionValue(company, ticker) {
  return `${company}${SELECTION_SEPARATOR}${ticker}`
}

/**
 * Inverse of buildSelectionValue:
 * receives "Company::TICKER" and returns { company, ticker }.
 */
function splitSelectionValue(value) {
  if (!value || typeof value !== 'string') {
    return { company: '', ticker: '' }
  }
  const [company, ticker] = value.split(SELECTION_SEPARATOR)
  return { company: company || '', ticker: ticker || '' }
}

/**
 * Tokenizes the query text into syntactic units:
 * - parentheses
 * - commas
 * - semicolons
 * - quoted strings
 * - plain words
 *
 * This step is generic and independent of the business semantics.
 */
function tokenize(input) {
  const tokens = []
  let index = 0
  while (index < input.length) {
    const char = input[index]

    // Skip whitespace
    if (/\s/.test(char)) {
      index += 1
      continue
    }

    // Simple punctuation symbols
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

    // Strings in single or double quotes, with escape support (\")
    if (char === '"' || char === "'") {
      const quote = char
      index += 1
      let buffer = ''
      let closed = false
      while (index < input.length) {
        const current = input[index]
        // Handle escaped character
        if (current === '\\' && index + 1 < input.length) {
          buffer += input[index + 1]
          index += 2
          continue
        }
        // Close string when matching quote is found
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

    // Accumulate a sequence of characters that forms a "word"
    let buffer = ''
    while (index < input.length && !/[\s(),;]/.test(input[index])) {
      buffer += input[index]
      index += 1
    }
    tokens.push({ type: 'WORD', value: buffer })
  }
  return tokens
}

/**
 * Walks down an AST node flattening binary nodes of the same type (AND/OR).
 * This makes it easier to build a linear list of clauses.
 */
function flattenNode(node, kind) {
  if (!node) return []
  if (node.type === kind) {
    return [...flattenNode(node.left, kind), ...flattenNode(node.right, kind)]
  }
  return [node]
}

/**
 * Converts the syntax tree (AST) into a list of normalized clauses.
 *
 * @param {object} node - current AST node
 * @param {'AND'|'OR'} parentLogical - logical operator inherited from the parent level
 * @returns {Array} list of clauses in the structure used by the store
 */
function astToClauses(node, parentLogical) {
  if (!node) {
    return []
  }

  // Base case: leaf node with a simple clause
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

  // Negation: creates a group with NOT
  if (node.type === 'NOT') {
    const innerClauses = astToClauses(node.operand, 'AND')
    return [
      {
        logical: 'NOT',
        group: { clauses: innerClauses },
      },
    ]
  }

  // Composite logical nodes (AND/OR)
  if (node.type === 'AND' || node.type === 'OR') {
    const nodeLogical = node.type === 'AND' ? 'AND' : 'OR'
    const children = flattenNode(node, node.type)
    const childClauses = children.flatMap((child) => astToClauses(child, nodeLogical))

    // If the external logical operator is the same, flatten into a single list
    if (parentLogical === nodeLogical) {
      return childClauses
    }

    // Otherwise, build a nested logical group
    return [
      {
        logical: parentLogical,
        group: { clauses: childClauses },
      },
    ]
  }

  throw new ParseError('Estrutura de consulta inválida.')
}

/**
 * Small recursive parser responsible for consuming tokens
 * and building the expression tree (AST).
 *
 * Grammar supports:
 * - OR, AND, NOT
 * - Parentheses for grouping
 * - Clauses of the form: field operator (values)
 */
class QueryParser {
  /**
   * @param {Array} tokens - sequence of tokens produced by tokenize()
   */
  constructor(tokens) {
    this.tokens = tokens
    this.current = 0
  }

  /**
   * Entry point of the parser.
   * Ensures that all tokens have been consumed or throws an error.
   */
  parse() {
    if (this.tokens.length === 0) {
      // Empty query: no filters
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

  /**
   * expression := or (';' or)*
   * Semicolon behaves as "AND" between blocks.
   */
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

  /**
   * or := and (OR and)*
   */
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

  /**
   * and := unary (AND unary)*
   */
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

  /**
   * unary := NOT unary | '(' expression ')' | clause
   */
  parseUnary() {
    // Step 1: handle NOT operator recursively
    if (this.matchLogical('NOT')) {
      const operand = this.parseUnary()
      if (!operand) {
        throw new ParseError('Esperado expressão após NOT.')
      }
      return { type: 'NOT', operand }
    }

    // Step 2: handle grouped expressions inside parentheses
    if (this.match('LPAREN')) {
      const expression = this.parseExpression()
      this.consume('RPAREN', 'Esperado ) para fechar o grupo.')
      return expression
    }

    // Step 3: base case, parse a simple clause
    return this.parseClause()
  }

  /**
   * clause := [logical*] field operator '(' values ')'
   *
   * Responsibilities:
   * - ignore redundant leading logical operators (AND, OR)
   * - validate field, operator and value count
   */
  parseClause() {
    // 1) Ignore redundant logical prefixes inside the clause (AND, OR)
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

    // 2) Company field (required)
    const fieldToken = this.consumeWord('Informe o campo da companhia.')
    const field = normalizeField(fieldToken.value)
    if (!field) {
      throw new ParseError(`Campo desconhecido: ${fieldToken.value}`)
    }

    // 3) Comparison operator (required)
    const operatorToken = this.consumeWord('Informe o operador de comparação.')
    const operator = normalizeOperator(operatorToken.value)
    if (!operator) {
      throw new ParseError(`Operador inválido: ${operatorToken.value}`)
    }

    // 4) List of values inside parentheses
    this.consume('LPAREN', 'Esperado ( para iniciar a lista de valores.')
    const values = []
    if (this.check('RPAREN')) {
      // Empty list: () directly
      this.advance()
    } else {
      // Read comma-separated values until ')'
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

    // 5) Normalize values (booleans, trims, etc.)
    const normalizedValues = normalizeValues(values)

    // 6) Business rule: minimum number of values
    if (!normalizedValues.length && !['CONTAINS', 'STARTS_WITH'].includes(operator)) {
      throw new ParseError(`Informe pelo menos um valor para ${field}.`)
    }

    // 7) Business rule: BETWEEN requires exactly 2 values
    if (operator === 'BETWEEN' && normalizedValues.length !== 2) {
      throw new ParseError(`O operador BETWEEN exige dois valores para ${field}.`)
    }

    // 8) Return clause node for the AST
    return {
      type: 'CLAUSE',
      field,
      operator,
      values: normalizedValues,
    }
  }

  /**
   * Consumes the next token if it matches the expected type.
   */
  match(type) {
    if (!this.check(type)) {
      return false
    }
    this.advance()
    return true
  }

  /**
   * Consumes the next token if it represents
   * a specific logical operator (AND/OR/NOT).
   */
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

  /**
   * Ensures that the next token has the expected type or throws a parse error.
   */
  consume(type, message) {
    if (this.check(type)) {
      return this.advance()
    }
    throw new ParseError(message)
  }

  /**
   * Ensures that the next token is a WORD or throws an error.
   */
  consumeWord(message) {
    const token = this.peek()
    if (!token || token.type !== 'WORD') {
      throw new ParseError(message)
    }
    this.advance()
    return token
  }

  /**
   * Reads a value inside the value list:
   * - if STRING, returns it as is
   * - if WORD, consumes a sequence of WORDs to allow multi-word values without quotes
   */
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
      // Consume adjacent words to allow values with spaces without quotes
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

  /**
   * Checks if the next token is of the given type.
   */
  check(type) {
    if (this.isAtEnd()) {
      return false
    }
    return this.peek().type === type
  }

  /**
   * Advances the read cursor by one token and returns the previous token.
   */
  advance() {
    if (!this.isAtEnd()) {
      this.current += 1
    }
    return this.previous()
  }

  /**
   * Returns the current token without consuming it.
   */
  peek() {
    return this.tokens[this.current]
  }

  /**
   * Returns the last consumed token.
   */
  previous() {
    return this.tokens[this.current - 1]
  }

  /**
   * Indicates whether we reached the end of the token list.
   */
  isAtEnd() {
    return this.current >= this.tokens.length
  }
}

/**
 * High-level function that converts query text into a normalized structure.
 * It isolates the flow: text -> tokens -> AST -> clauses.
 */
function parseTextToQuery(text) {
  try {
    const tokens = tokenize(text)
    const parser = new QueryParser(tokens)
    const ast = parser.parse()
    if (!ast) {
      // Empty query
      return { clauses: [] }
    }
    const clauses = astToClauses(ast, 'AND')
    return { clauses }
  } catch (error) {
    if (error instanceof ParseError) {
      // Syntax errors are rethrown so the caller can show a friendly message
      throw error
    }
    // Any other error is turned into a generic user-facing message
    throw new ParseError('Não foi possível interpretar a consulta fornecida.')
  }
}

/**
 * Central company store.
 * Responsibilities:
 * - keep structured query and free-text representation
 * - call the API to search companies
 * - manage facets and sector/subsector/segment cascade
 * - control the selection of Company::Ticker pairs
 */
export const useCompanyStore = defineStore('companyStore', {
  /**
   * Main reactive state for the company domain.
   */
  state: () => ({
    // Normalized query structure (parser output)
    filterQuery: { clauses: [] },

    // Free text typed by the user in the advanced search box
    queryText: '',

    // List of companies returned by the last search
    companies: [],

    // Total number of companies found by the API (for future pagination)
    total: 0,

    // Aggregated facets/counts for filters (e.g., by sector, segment)
    facets: {},

    // Current user selection: ["Company::TICKER", ...]
    selectedItems: [],

    // UI state flags
    isLoading: false,
    error: null,

    // Sector → Subsector → Segment cascade structure
    // Used to populate dependent dropdowns in the UI.
    industryCascade: {
      sectorToSubsectors: {},
      sectorToSegments: {},
      subsectorToSegments: {},
    },
  }),

  /**
   * Getters are derived views over state:
   * they compute useful maps and structures for components.
   */
  getters: {
    /**
     * Returns a map field → corresponding clause in the query.
     * Allows the UI to quickly detect whether a filter already exists for a field.
     */
    clauseByField(state) {
      const map = {}
      for (const clause of state.filterQuery.clauses || []) {
        if (clause.condition && clause.condition.field) {
          map[clause.condition.field] = clause
        }
      }
      return map
    },

    /**
     * Converts selectedItems (strings "Company::Ticker")
     * into structured pairs { company, ticker }.
     */
    selectedPairs(state) {
      return (state.selectedItems || []).map(splitSelectionValue)
    },

    selectedValuesByField(state) {
      const result = {}
      for (const clause of state.filterQuery.clauses || []) {
        if (!clause?.condition?.field) continue
        result[clause.condition.field] = clause.condition.values || []
      }
      return result
    },

    facetOptions(state) {
      return state.facets || {}
    },
  },

  /**
   * Actions encapsulate all logic that mutates state:
   * they call external services, apply business rules and update the state.
   */
  actions: {
    /**
     * Updates a facet-based filter for a specific field (e.g., sector, segment).
     * Steps:
     * 1) normalize field, logical operator and values
     * 2) remove any existing clause for the same field
     * 3) add a new clause if there are values
     * 4) sync queryText with the normalized structure
     */
    setFacetSelection(field, logical, values, operator = DEFAULT_OPERATOR) {
      // 1) Normalize raw inputs to keep the internal API consistent
      const normalizedField = normalizeField(field) || field
      const normalizedLogical = 'AND'
      const normalizedValues = normalizeValues(values)
      const normalizedOperator = normalizeOperator(operator) || DEFAULT_OPERATOR

      // 2) Create an immutable copy of the existing clauses
      const clauses = cloneClauses(this.filterQuery.clauses || [])

      // 3) Remove any previous clause for the same field
      const filteredClauses = clauses.filter(
        (clause) => !clause.condition || clause.condition.field !== normalizedField,
      )

      // 4) If there are values, append a new facet clause
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

      // 5) Update the query structure and its textual representation
      this.filterQuery = { clauses: filteredClauses }
      this.queryText = this.serializeQuery(this.filterQuery)
    },

    /**
     * Updates only the free-text query.
     * Parsing is not triggered automatically to keep responsibilities separated.
     */
    setQueryText(text) {
      this.queryText = text
    },

    /**
     * Applies the free-text query:
     * 1) tries to parse it
     * 2) on success, updates filterQuery and normalizes queryText
     * 3) triggers a company reload
     * 4) returns a result object so the UI can handle success/error
     */
    applyQueryText() {
      try {
        // 1) Convert text into normalized structure
        const parsed = this.parseQuery(this.queryText)

        // 2) Update structured query and rewrite text in canonical form
        this.filterQuery = parsed
        this.queryText = this.serializeQuery(parsed)

        // 3) Reload companies with the new query
        this.loadCompanies()
        return { ok: true }
      } catch (error) {
        // 4) Translate parsing errors into a friendly message
        const message = error instanceof ParseError ? error.message : 'Consulta inválida.'
        return { ok: false, message }
      }
    },

    /**
     * Resets filters and selection:
     * 1) clears structured query and text
     * 2) clears item selection
     * 3) reloads companies with an "empty" filter
     */
    resetFilters() {
      this.filterQuery = { clauses: [] }
      this.queryText = ''
      this.selectedItems = []
      this.loadCompanies()
    },

    /**
     * Updates the list of items selected by the user.
     * Ensures all entries are non-empty strings.
     */
    setSelectedItems(values) {
      const normalized = Array.isArray(values)
        ? values.map((value) => String(value)).filter((value) => value.length)
        : []
      this.selectedItems = normalized
    },

    /**
     * Main flow to load companies from the API.
     * Responsibilities:
     * 1) set loading flag
     * 2) call searchCompanies with the current filterQuery
     * 3) populate companies list and total
     * 4) rebuild sector/subsector/segment cascade
     * 5) prune invalid selections
     * 6) sync queryText if it is empty
     * 7) handle network/server errors
     */
    async loadCompanies() {
      // 1) Signal to the UI that an async operation is in progress
      this.isLoading = true
      this.error = null

      try {
        // 2) Call search service with the current structured query
        const payload = await searchCompanies(this.filterQuery)

        // 3) Update companies list and total result count
        this.companies = payload.items || []
        this.total = payload.total || 0

        // 4) Rebuild sector/subsector/segment cascade from the new list
        this._rebuildIndustryCascade(this.companies)

        // 5) Remove from selection any item that no longer exists in the current list
        this._pruneSelection()

        // 6) If queryText is empty, sync it with the normalized structure
        if (!this.queryText) {
          this.queryText = this.serializeQuery(this.filterQuery)
        }
      } catch (err) {
        // 7) Log diagnostic info and set a user-friendly error message
        console.error(err)
        this.error = 'Falha ao carregar companhias'
      } finally {
        // 8) Ensure loading flag is reset even if an error happens
        this.isLoading = false
      }
    },

    /**
     * Loads company facets (aggregations for filters).
     * This operation is independent from the main search.
     */
    async loadFacets() {
      try {
        const payload = await fetchCompanyFacets()
        this.facets = payload.facets || {}
      } catch (err) {
        console.error(err)
      }
    },

    async loadFacetsForCurrentQuery() {
      try {
        const payload = await fetchCompanyFacetsForQuery(this.filterQuery)
        this.facets = payload.facets || {}
      } catch (err) {
        console.error(err)
      }
    },

    /**
     * Serializes a normalized query into a textual string.
     * This is the inverse path of parseQuery.
     */
    serializeQuery(query) {
      if (!query || !Array.isArray(query.clauses) || query.clauses.length === 0) {
        return ''
      }
      return serializeClauses(query.clauses)
    },

    /**
     * Converts free text into a normalized query structure.
     * This wraps parseTextToQuery so the implementation can change later.
     */
    parseQuery(text) {
      if (!text || !text.trim()) {
        return { clauses: [] }
      }
      return parseTextToQuery(text)
    },

    /**
     * Builds the Sector → Subsector → Segment cascade structure
     * from the currently loaded company list.
     *
     * Goal: feed dependent combos in the front-end
     * without spreading domain knowledge across components.
     */
    _rebuildIndustryCascade(items = []) {
      // 1) Use Maps + Sets to avoid duplicates
      const sectorToSubsectors = new Map()
      const sectorToSegments = new Map()
      const subsectorToSegments = new Map()

      for (const company of items || []) {
        // 2) Extract domain fields used in the cascade
        const sector = (company.sector || '').trim()
        const subsector = (company.subsector || '').trim()
        const segment = (company.segment || '').trim()

        // 3) If the company has none of these attributes, skip it
        if (!sector && !subsector && !segment) continue

        // 4) Ensure initial collections exist for each sector
        if (sector) {
          if (!sectorToSubsectors.has(sector)) {
            sectorToSubsectors.set(sector, new Set())
          }
          if (!sectorToSegments.has(sector)) {
            sectorToSegments.set(sector, new Set())
          }
        }

        // 5) Ensure initial collections exist for each subsector
        if (subsector) {
          if (!subsectorToSegments.has(subsector)) {
            subsectorToSegments.set(subsector, new Set())
          }
        }

        // 6) Link sector → subsector
        if (sector && subsector) {
          sectorToSubsectors.get(sector).add(subsector)
        }

        // 7) Link sector → segment (for 2-level combos)
        if (sector && segment) {
          sectorToSegments.get(sector).add(segment)
        }

        // 8) Link subsector → segment (for alternative 2-level combos)
        if (subsector && segment) {
          subsectorToSegments.get(subsector).add(segment)
        }
      }

      /**
       * Converts Map<key, Set<value>> into a plain object:
       * - filters out empty values
       * - sorts values alphabetically using pt-BR locale
       */
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

      // 9) Update the reactive cascade structure as plain objects
      this.industryCascade = {
        sectorToSubsectors: normalizeMap(sectorToSubsectors),
        sectorToSegments: normalizeMap(sectorToSegments),
        subsectorToSegments: normalizeMap(subsectorToSegments),
      }
    },

    /**
     * Ensures that selectedItems only contains valid pairs
     * that still exist in the currently loaded company list.
     *
     * This prevents the user from keeping selections that disappeared
     * after changing filters.
     */
    _pruneSelection() {
      // 1) If there is no selection, there is nothing to prune
      if (!this.selectedItems || this.selectedItems.length === 0) {
        return
      }

      // 2) Build a set of valid selections based on current companies
      const valid = new Set()
      for (const company of this.companies || []) {
        const companyName = company.company_name || ''
        for (const ticker of company.tickers || []) {
          if (!ticker) continue
          valid.add(buildSelectionValue(companyName, ticker))
        }
      }

      // 3) Keep only items that still exist as valid combinations
      const filtered = this.selectedItems.filter((value) => valid.has(value))

      // 4) If pruning happened, update the reactive selection
      if (filtered.length !== this.selectedItems.length) {
        this.selectedItems = filtered
      }
    },
  },
})

export { ParseError }
