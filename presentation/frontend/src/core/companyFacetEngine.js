import { bucketsToOptions } from './facetEngine'

function getCompanySector(company) {
  const raw =
    company.sectorCode ??
    company.industry_sector_code ??
    company.industry_sector ??
    company.sector
  return raw ? String(raw).trim() : ''
}

function getCompanySubsector(company) {
  const raw =
    company.subsectorCode ??
    company.industry_subsector_code ??
    company.industry_subsector ??
    company.subsector
  return raw ? String(raw).trim() : ''
}

function getCompanySegment(company) {
  const raw =
    company.segmentCode ??
    company.industry_segment_code ??
    company.industry_segment ??
    company.segment
  return raw ? String(raw).trim() : ''
}

export function applyCompanyFilter(companies, filter) {
  const { sector = [], subsector = [], segment = [] } = filter || {}
  const selectedSector = sector
    .map((value) => String(value || '').trim())
    .filter(Boolean)
  const selectedSubsector = subsector
    .map((value) => String(value || '').trim())
    .filter(Boolean)
  const selectedSegment = segment
    .map((value) => String(value || '').trim())
    .filter(Boolean)

  return (companies || []).filter((company) => {
    const sectorKey = getCompanySector(company)
    const subsectorKey = getCompanySubsector(company)
    const segmentKey = getCompanySegment(company)

    const matchSector = !selectedSector.length || selectedSector.includes(sectorKey)
    const matchSubsector =
      !selectedSubsector.length || selectedSubsector.includes(subsectorKey)
    const matchSegment = !selectedSegment.length || selectedSegment.includes(segmentKey)

    return matchSector && matchSubsector && matchSegment
  })
}

export function buildCompanyFacets(companies) {
  const sectorBuckets = new Map()
  const subsectorBuckets = new Map()
  const segmentBuckets = new Map()

  for (const company of companies || []) {
    const sectorKey = getCompanySector(company)
    const sectorLabel =
      company.sectorName ?? company.industry_sector_name ?? company.industry_sector

    const subsectorKey = getCompanySubsector(company)
    const subsectorLabel =
      company.subsectorName ?? company.industry_subsector_name ?? company.industry_subsector

    const segmentKey = getCompanySegment(company)
    const segmentLabel =
      company.segmentName ?? company.industry_segment_name ?? company.industry_segment

    if (sectorKey) {
      sectorBuckets.set(sectorKey, {
        key: sectorKey,
        label: sectorLabel ?? sectorKey,
        count: (sectorBuckets.get(sectorKey)?.count || 0) + 1,
      })
    }

    if (subsectorKey) {
      subsectorBuckets.set(subsectorKey, {
        key: subsectorKey,
        label: subsectorLabel ?? subsectorKey,
        count: (subsectorBuckets.get(subsectorKey)?.count || 0) + 1,
      })
    }

    if (segmentKey) {
      segmentBuckets.set(segmentKey, {
        key: segmentKey,
        label: segmentLabel ?? segmentKey,
        count: (segmentBuckets.get(segmentKey)?.count || 0) + 1,
      })
    }
  }

  const sectorOptions = bucketsToOptions([...sectorBuckets.values()])
  const subsectorOptions = bucketsToOptions([...subsectorBuckets.values()])
  const segmentOptions = bucketsToOptions([...segmentBuckets.values()])

  sectorOptions.sort((a, b) => a.label.localeCompare(b.label))
  subsectorOptions.sort((a, b) => a.label.localeCompare(b.label))
  segmentOptions.sort((a, b) => a.label.localeCompare(b.label))

  return {
    sector: sectorOptions,
    subsector: subsectorOptions,
    segment: segmentOptions,
  }
}
