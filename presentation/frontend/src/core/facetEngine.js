export function bucketsToOptions(buckets = []) {
  return (buckets || [])
    .map((bucket) => {
      const key = bucket?.key
      if (key === undefined || key === null || String(key).length === 0) {
        return null
      }
      const label = bucket?.label ?? String(key)
      return {
        value: String(key),
        label: String(label),
        count: bucket?.count ?? 0,
      }
    })
    .filter(Boolean)
}
