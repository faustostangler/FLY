export function buildFacetBuckets(companies, facetFields) {
  const buckets = {}
  for (const field of facetFields) {
    buckets[field] = new Map()
  }

  for (const company of companies || []) {
    for (const field of facetFields) {
      const raw = company[field] ?? ''
      const value = String(raw).trim()
      if (!value) continue

      if (!buckets[field].has(value)) {
        buckets[field].set(value, 0)
      }
      buckets[field].set(value, buckets[field].get(value) + 1)
    }
  }

  return buckets
}

export function bucketsToOptions(buckets) {
  const result = {}
  for (const [field, map] of Object.entries(buckets)) {
    result[field] = Array.from(map.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([value, count]) => ({ value, label: value, count }))
  }
  return result
}
