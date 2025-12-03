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

export function buildChartFilterTree(filterQuery) {
  if (!filterQuery || !Array.isArray(filterQuery.clauses)) {
    return null
  }

  const andClauses = []
  const orClauses = []
  const notClauses = []

  for (const clause of filterQuery.clauses) {
    if (!clause || !clause.condition) {
      continue
    }

    const leaf = buildLeaf(clause.condition)
    if (!leaf) {
      continue
    }

    const logical = String(clause.logical || 'AND').toUpperCase()
    if (logical === 'OR') {
      orClauses.push(leaf)
    } else if (logical === 'NOT') {
      notClauses.push({ not: leaf })
    } else {
      andClauses.push(leaf)
    }
  }

  let tree = null

  if (andClauses.length === 1) {
    tree = andClauses[0]
  } else if (andClauses.length > 1) {
    tree = { and: andClauses }
  }

  if (orClauses.length === 1) {
    tree = tree ? { and: [tree, orClauses[0]] } : orClauses[0]
  } else if (orClauses.length > 1) {
    const orNode = { or: orClauses }
    tree = tree ? { and: [tree, orNode] } : orNode
  }

  if (notClauses.length === 1) {
    tree = tree ? { and: [tree, notClauses[0]] } : notClauses[0]
  } else if (notClauses.length > 1) {
    const notNode = { and: notClauses }
    tree = tree ? { and: [tree, notNode] } : notNode
  }

  return tree
}

