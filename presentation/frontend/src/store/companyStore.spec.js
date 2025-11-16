import { describe, expect, it } from 'vitest'
import { buildFilterQueryFromFacets } from './companyStore'

describe('buildFilterQueryFromFacets', () => {
  it('builds AND/IN clauses using facet fields', () => {
    const query = buildFilterQueryFromFacets({
      industry_sector: ['Financeiro', 'Energia'],
      market: new Set(['BDR']),
    })

    expect(query.clauses).toEqual([
      {
        logical: 'AND',
        condition: {
          field: 'industry_sector',
          operator: 'IN',
          values: ['Financeiro', 'Energia'],
        },
      },
      {
        logical: 'AND',
        condition: {
          field: 'market',
          operator: 'IN',
          values: ['BDR'],
        },
      },
    ])
  })

  it('ignores unknown facets and empty selections', () => {
    const query = buildFilterQueryFromFacets({
      unknown: ['value'],
      market: [],
      code: [' ABC ', '', null],
    })

    expect(query.clauses).toEqual([
      {
        logical: 'AND',
        condition: {
          field: 'code',
          operator: 'IN',
          values: ['ABC'],
        },
      },
    ])
  })
})
