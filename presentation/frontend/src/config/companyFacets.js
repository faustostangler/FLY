export const COMPANY_FACETS = [
  // --- Campos textuais SINGLE -----------------------------------------------------
  { field: 'industry_sector', label: 'Setor', type: 'text', multiple: true, searchable: true },
  { field: 'industry_subsector', label: 'Subsetor', type: 'text', multiple: true, searchable: true },
  { field: 'industry_segment', label: 'Segmento', type: 'text', multiple: true, searchable: true },
  { field: 'company_name', label: 'Companhia', type: 'text', multiple: true, searchable: true },
  { field: 'trading_name', label: 'Nome de Pregão', type: 'text', multiple: true, searchable: true },
  { field: 'issuing_company', label: 'Código', type: 'text', multiple: true, searchable: true },
  { field: 'code', label: 'Ticker', type: 'text', multiple: true, searchable: true },
  { field: 'cnpj', label: 'CNPJ', type: 'text', multiple: true, searchable: true },
  // { field: 'website', label: 'Website', type: 'text', multiple: true, searchable: true },
 
  // --- Campos textuais MULTIPLE  -----------------------------------------------------
  // { field: 'company_segment', label: 'Segmento da Companhia', type: 'text', multiple: true, searchable: true },
  // { field: 'company_segment_eng', label: 'Segmento da Companhia (EN)', type: 'text', multiple: true, searchable: true },
  // { field: 'activity', label: 'Atividade', type: 'text', multiple: true, searchable: true },
  { field: 'market', label: 'Mercado', type: 'text', multiple: true, searchable: true },
  { field: 'institution_common', label: 'Instituição Ordinária', type: 'text', multiple: true, searchable: true },
  { field: 'institution_preferred', label: 'Instituição Preferencial', type: 'text', multiple: true, searchable: true },
  
  // --- Campos textuais LEGACY  -----------------------------------------------------
  // { field: 'industry_classification', label: 'Classificação', type: 'text', multiple: true, searchable: true },
  // { field: 'industry_classification_eng', label: 'Classificação (EN)', type: 'text', multiple: true, searchable: true },
  // { field: 'company_category', label: 'Categoria', type: 'text', multiple: true, searchable: true },
  // { field: 'company_type', label: 'Tipo', type: 'text', multiple: true, searchable: true },
  // { field: 'listing_segment', label: 'Segmento de Listagem', type: 'text', multiple: true, searchable: true },
  // { field: 'registrar', label: 'Escriturador', type: 'text', multiple: true, searchable: true },
  // { field: 'status', label: 'Status', type: 'text', multiple: true, searchable: true },
  // { field: 'market_indicator', label: 'Indicador de Mercado', type: 'text', multiple: true, searchable: true },
  // { field: 'type_bdr', label: 'Tipo de BDR', type: 'text', multiple: true, searchable: true },
  // { field: 'reason', label: 'Motivo', type: 'text', multiple: true, searchable: true },

  // --- Booleanos -----------------------------------------------------------
  // {
    // field: 'has_bdr',
    // label: 'Tem BDR',
    // type: 'boolean',
    // multiple: false,
    // options: [
    //   { value: 'true', label: 'Sim' },
    //   { value: 'false', label: 'Não' },
    // ],
  // },
  // {
  //   field: 'has_quotation',
  //   label: 'Tem Cotação',
  //   type: 'boolean',
  //   multiple: false,
  //   options: [
  //     { value: 'true', label: 'Sim' },
  //     { value: 'false', label: 'Não' },
  //   ],
  // },
  // {
  //   field: 'has_emissions',
  //   label: 'Tem Emissões',
  //   type: 'boolean',
  //   multiple: false,
  //   options: [
  //     { value: 'true', label: 'Sim' },
  //     { value: 'false', label: 'Não' },
  //   ],
  // },

  // --- Datas ---------------------------------------------------------------
  // { field: 'date_quotation', label: 'Data de Cotação', type: 'date-range', multiple: false },
  // { field: 'last_date', label: 'Última Data', type: 'date-range', multiple: false },
  // { field: 'listing_date', label: 'Data de Listagem', type: 'date-range', multiple: false },
]
