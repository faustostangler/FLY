import { describe, expect, it } from 'vitest'
import { applyFacetFilters, recomputeFacets } from './facetEngine'

const companies = [
  {
    id: 1,
    industry_sector: 'Financeiro',
    industry_subsector: 'Bancos',
    industry_segment: 'Banco Múltiplo',
    listing_segment: 'Novo Mercado',
    company_name: 'Banco Azul',
    trading_name: 'Banco Azul',
    issuing_company: '001',
    code: 'AZUL3',
    cnpj: '111',
    market: 'Ações',
    institution_common: 'XPTO',
    institution_preferred: 'YPTO',
  },
  {
    id: 2,
    industry_sector: 'Energia',
    industry_subsector: 'Eletricidade',
    industry_segment: 'Geração',
    listing_segment: 'Nível 2',
    company_name: 'Eletro Luz',
    trading_name: 'Eletro Luz',
    issuing_company: '002',
    code: 'ELUZ3',
    cnpj: '222',
    market: 'Ações',
    institution_common: 'Zeta',
    institution_preferred: 'Zeta',
  },
  {
    id: 3,
    industry_sector: 'Financeiro',
    industry_subsector: 'Seguros',
    industry_segment: 'Seguradora',
    listing_segment: 'Nível 2',
    company_name: 'Seguradora Verde',
    trading_name: 'Seguradora Verde',
    issuing_company: '003',
    code: 'VERD3',
    cnpj: '333',
    market: 'BDR',
    institution_common: 'Gamma',
    institution_preferred: 'Gamma',
  },
]

describe('applyFacetFilters', () => {
  it('returns all companies when no filters are provided', () => {
    const filtered = applyFacetFilters(companies, {})
    expect(filtered).toHaveLength(3)
  })

  it('filters companies by selected facet values', () => {
    const filtered = applyFacetFilters(companies, { industry_sector: ['Financeiro'] })
    expect(filtered.map((c) => c.id)).toEqual([1, 3])
  })
})

describe('recomputeFacets', () => {
  it('builds facet options from the filtered dataset', () => {
    const { filteredCompanies, facetOptions } = recomputeFacets({
      companies,
      activeFacetFilters: {},
    })

    expect(filteredCompanies).toHaveLength(3)
    expect(facetOptions.industry_sector.map((o) => o.value)).toContain('Financeiro')
    expect(facetOptions.industry_sector.map((o) => o.value)).toContain('Energia')
    expect(facetOptions.industry_subsector.map((o) => o.value)).toEqual(
      expect.arrayContaining(['Bancos', 'Eletricidade', 'Seguros']),
    )
  })

  it('keeps facets consistent when filters are applied', () => {
    const { filteredCompanies, facetOptions } = recomputeFacets({
      companies,
      activeFacetFilters: {
        industry_sector: ['Financeiro'],
      },
    })

    expect(filteredCompanies).toHaveLength(2)
    expect(facetOptions.industry_subsector.map((o) => o.value)).toEqual(
      expect.arrayContaining(['Bancos', 'Seguros']),
    )
    expect(facetOptions.industry_segment.map((o) => o.value)).toEqual(
      expect.arrayContaining(['Banco Múltiplo', 'Seguradora']),
    )
    expect(facetOptions.listingSegment?.map((o) => o.value)).toEqual(
      expect.arrayContaining(['Novo Mercado', 'Nível 2']),
    )
  })

  it('applies new facets to constrain the available options', () => {
    const { filteredCompanies, facetOptions } = recomputeFacets({
      companies,
      activeFacetFilters: {
        listingSegment: ['Nível 2'],
      },
    })

    expect(filteredCompanies).toHaveLength(2)
    expect(facetOptions.industry_sector.map((o) => o.value)).toEqual(
      expect.arrayContaining(['Energia', 'Financeiro']),
    )
    expect(facetOptions.industry_subsector.map((o) => o.value)).not.toContain('Bancos')
  })
})
