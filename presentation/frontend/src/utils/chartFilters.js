const OPERATOR_MAP = {
  EQUALS: 'eq',
  IN: 'in',
  NE: 'ne',
  CONTAINS: 'contains',
  STARTS_WITH: 'startswith',
  ENDS_WITH: 'endswith',
  GT: 'gt',
  GTE: 'gte',
  LT: 'lt',
  LTE: 'lte',
  BETWEEN: 'between',
}

function normalizeValues(values) {
  if (!Array.isArray(values)) {
    return []
  }
  return values
    .map((value) => {
      if (value === null || value === undefined) {
        return ''
      }
      return String(value).trim()
    })
    .filter(Boolean)
}

function buildConditionLeaf(condition) {
  if (!condition || !condition.field) {
    return null
  }
  const field = condition.field
  const operator = String(condition.operator || '').toUpperCase()
  const op = OPERATOR_MAP[operator] || 'eq'
  const values = normalizeValues(condition.values)

  if (!values.length) {
    return null
  }

  if (op === 'eq' && values.length === 1) {
    return { [field]: values[0] }
  }
  if (op === 'in' || op === 'eq') {
    return { [field]: { in: values } }
  }
  if (op === 'between' && values.length === 2) {
    return { [field]: { between: values } }
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
    const leaf = buildConditionLeaf(clause.condition)
    if (!leaf) {
      continue
    }

    const logical = String(clause.logical || 'AND').toUpperCase()
    if (logical === 'AND') {
      andClauses.push(leaf)
    } else if (logical === 'OR') {
      orClauses.push(leaf)
    } else if (logical === 'NOT') {
      notClauses.push({ not: leaf })
    }
  }

  const tree = {}
  if (andClauses.length === 1) {
    Object.assign(tree, andClauses[0])
  } else if (andClauses.length > 1) {
    tree.and = andClauses
  }

  if (orClauses.length === 1) {
    const orNode = orClauses[0]
    if (tree.and) {
      tree.and.push(orNode)
    } else if (Object.keys(tree).length) {
      tree.and = [tree, orNode]
    } else {
      Object.assign(tree, orNode)
    }
  } else if (orClauses.length > 1) {
    const orNode = { or: orClauses }
    if (tree.and) {
      tree.and.push(orNode)
    } else if (Object.keys(tree).length) {
      tree.and = [tree, orNode]
    } else {
      Object.assign(tree, orNode)
    }
  }

  if (notClauses.length === 1) {
    const notNode = notClauses[0]
    if (tree.and) {
      tree.and.push(notNode)
    } else if (Object.keys(tree).length) {
      tree.and = [tree, notNode]
    } else {
      Object.assign(tree, notNode)
    }
  } else if (notClauses.length > 1) {
    const notNode = { and: notClauses }
    if (tree.and) {
      tree.and.push(notNode)
    } else if (Object.keys(tree).length) {
      tree.and = [tree, notNode]
    } else {
      Object.assign(tree, notNode)
    }
  }

  return Object.keys(tree).length ? tree : null
}
