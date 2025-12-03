export function extractTicker(value) {
  if (value == null) {
    return ''
  }
  const raw = String(value).trim()
  if (!raw) {
    return ''
  }
  const parts = raw.split('::')
  if (parts.length === 1) {
    return parts[0]
  }
  return parts[1] || ''
}

export function extractTickers(values) {
  if (!Array.isArray(values)) {
    return []
  }
  return values
    .map((value) => extractTicker(value))
    .filter((ticker) => ticker.length)
}
