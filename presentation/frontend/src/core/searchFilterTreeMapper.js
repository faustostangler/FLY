export function buildSearchFilterTree(filterQuery) {
  if (
    !filterQuery ||
    !Array.isArray(filterQuery.clauses) ||
    filterQuery.clauses.length === 0
  ) {
    return {}
  }

  const andChildren = []

  for (const clause of filterQuery.clauses) {
    const condition = clause.condition || {}
    const field = condition.field
    const operator = (condition.operator || 'IN').toUpperCase()
    const values = Array.isArray(condition.values) ? condition.values : []

    if (!field || values.length === 0) continue

    if (operator === 'IN') {
      if (values.length === 1) {
        andChildren.push({ [field]: values[0] })
      } else {
        andChildren.push({
          or: values.map((value) => ({ [field]: value })),
        })
      }
      continue
    }

    if (operator === 'GT' && values.length === 1) {
      andChildren.push({ [field]: { gt: values[0] } })
      continue
    }
  }

  if (andChildren.length === 0) {
    return {}
  }
  if (andChildren.length === 1) {
    return andChildren[0]
  }
  return { and: andChildren }
}
