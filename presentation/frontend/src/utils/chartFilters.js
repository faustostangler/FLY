const OPERATOR_MAP = {
  IN: 'in',
  EQUALS: 'eq',
  CONTAINS: 'contains',
  STARTS_WITH: 'startswith',
  ENDS_WITH: 'endswith',
  BETWEEN: 'between',
  GT: 'gt',
  GTE: 'gte',
  LT: 'lt',
  LTE: 'lte',
}

function normalizeValues(values) {
  return (Array.isArray(values) ? values : [values])
    .map((value) => {
      if (value === null || value === undefined) {
        return ''
      }
      return String(value).trim()
    })
    .filter(Boolean)
}

function buildLeaf(condition) {
  if (!condition || !condition.field) {
    return null
  }

  const field = condition.field
  const operator = String(condition.operator || '').toUpperCase()
  const values = normalizeValues(condition.values || [])

  if (!values.length) {
    return null
  }

  const op = OPERATOR_MAP[operator]

  if (!op || op === 'eq') {
    if (values.length === 1) {
      return { [field]: values[0] }
    }
    return { [field]: { in: values } }
  }

  if (op === 'in') {
    return { [field]: { in: values } }
  }

  if (op === 'between' && values.length >= 2) {
    return { [field]: { between: values.slice(0, 2) } }
  }

  if (['gt', 'gte', 'lt', 'lte'].includes(op)) {
    return { [field]: { [op]: values.length === 1 ? values[0] : values } }
  }

  return { [field]: { [op]: values.length === 1 ? values[0] : values } }
}

function buildGroup(clauses) {
  if (!clauses || !clauses.length) {
    return null
  }

  // Detecta a lógica predominante no grupo olhando para o primeiro item.
  // O parser do frontend (astToClauses) agrupa itens de lógica diferente em subgrupos,
  // então aqui devemos ter uma lista homogênea (ex: todos OR ou todos AND).
  const firstLogical = clauses[0].logical || 'AND'
  const key = firstLogical.toLowerCase() // 'and', 'or', 'not'

  const children = []

  for (const clause of clauses) {
    let child = null

    if (clause.group) {
      // Recursão para grupos aninhados
      child = buildGroup(clause.group.clauses)
    } else if (clause.condition) {
      // Folha
      child = buildLeaf(clause.condition)
    }

    if (child) {
      // Se o operador lógico deste item for NOT, envolvemos ele.
      // Nota: se a lista for toda NOT, teremos { "not": [...] } ?
      // O backend espera { "not": { ... } }.
      // Se tivermos múltiplos NOTs na lista, eles são AND NOT ou OR NOT?
      // O astToClauses trata NOT como um wrapper de um grupo ou condição.
      // Então clause.logical == 'NOT' geralmente envolve um único filho.

      if (clause.logical === 'NOT') {
        children.push({ not: child })
      } else {
        children.push(child)
      }
    }
  }

  if (!children.length) {
    return null
  }

  // Se a chave for 'not', o comportamento é diferente?
  // Geralmente 'not' não é uma lista de itens, mas um wrapper.
  // Mas aqui estamos processando uma lista.
  // Se firstLogical for NOT, significa que o primeiro item é NOT.
  // Mas se tivermos [NOT A, NOT B], isso é (NOT A) AND (NOT B)?
  // O astToClauses define o parentLogical.

  // Se firstLogical for NOT, vamos assumir que é uma lista de negações combinadas por AND (default).
  // Mas na verdade, o buildGroup deve retornar o container.
  // Se os itens são {not: A}, {not: B}, eles já estão embrulhados.
  // O container deve ser AND ou OR.

  // CORREÇÃO: O `logical` no clause diz como ele se conecta ao ANTERIOR (ou ao pai).
  // Se temos [ {logical: OR, ...}, {logical: OR, ...} ], o grupo é OR.
  // Se temos [ {logical: NOT, ...} ], o grupo é... ?
  // O astToClauses gera NOT sempre como um wrapper único:
  // { logical: 'NOT', group: { clauses: [...] } }
  // Então dentro desse grupo, as clauses terão a lógica interna (AND/OR).
  // O wrapper em si tem logical NOT.

  // Então, se estamos processando uma lista de clauses, elas devem ser AND ou OR.
  // O caso NOT é tratado no loop (envolvendo o child).
  // O container da lista deve ser AND ou OR.

  // Se firstLogical for NOT, isso é estranho para uma lista, a menos que seja um item único.
  // Mas vamos assumir AND se não for OR.

  const containerKey = (firstLogical === 'OR') ? 'or' : 'and'

  if (children.length === 1) {
    return children[0]
  }

  return { [containerKey]: children }
}

export function buildChartFilterTree(filterQuery) {
  if (!filterQuery || !Array.isArray(filterQuery.clauses)) {
    return null
  }

  // A raiz do filterQuery é implicitamente um AND de todas as cláusulas
  return buildGroup(filterQuery.clauses)
}

