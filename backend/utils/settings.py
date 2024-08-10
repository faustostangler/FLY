import re

# System-wide settings
batch_size = 50  # Batch size for data processing
num_batches = 8
big_batch_size = int(40000 / num_batches)
db_name = 'b3.db'  # Database name
db_folder = 'backend/data'  # Folder where the database is stored
db_folder_short = 'data'
finsheet_types = ["DEMONSTRACOES FINANCEIRAS PADRONIZADAS", "INFORMACOES TRIMESTRAIS"]
findata = [
    ['DFs Consolidadas', 'Demonstração do Resultado'], 
    ['DFs Consolidadas', 'Balanço Patrimonial Ativo'], 
    ['DFs Consolidadas', 'Balanço Patrimonial Passivo'], 
    ['DFs Consolidadas', 'Demonstração do Fluxo de Caixa'], 
    ['DFs Consolidadas', 'Demonstração de Valor Adicionado'], 
    ['DFs Individuais', 'Demonstração do Resultado'], 
    ['DFs Individuais', 'Balanço Patrimonial Ativo'], 
    ['DFs Individuais', 'Balanço Patrimonial Passivo'], 
    ['DFs Individuais', 'Demonstração do Fluxo de Caixa'], 
    ['DFs Individuais', 'Demonstração de Valor Adicionado'], 
]
fincapital = [
    ['Dados da Empresa', 'Composição do Capital'], 
]
last_quarters = ['3', '4']
all_quarters = ['6', '7']
cols_b3 = ['nsd', 'tipo', 'setor', 'subsetor', 'segmento', 'company_name', 'quadro', 'quarter', 'conta', 'descricao', 'valor', 'version']
cols_order = ['tipo', 'company_name', 'conta', 'quarter']

# Selenium settings
wait_time = 2  # Wait time for Selenium operations
driver = driver_wait = None  # Placeholders for Selenium driver and wait objects

# B3 information
companies_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/search?language=pt-br"  # URL for the B3 companies search page
company_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/?language=pt-br"  # URL for the B3 company detail page

# List of judicial terms to be removed from company names
judicial = [
    '  EM LIQUIDACAO', ' EM LIQUIDACAO', ' EXTRAJUDICIAL', 
    '  EM RECUPERACAO JUDICIAL', '  EM REC JUDICIAL', 
    ' EM RECUPERACAO JUDICIAL', ' EM LIQUIDACAO EXTRAJUDICIAL', ' EMPRESA FALIDA', 
]
# Regular expression pattern to remove judicial terms from company names
words_to_remove = '|'.join(map(re.escape, judicial))

# Dictionary mapping governance level abbreviations to their full descriptions
governance_levels = {
    "NM": "Cia. Novo Mercado",
    "N1": "Cia. Nível 1 de Governança Corporativa",
    "N2": "Cia. Nível 2 de Governança Corporativa",
    "MA": "Cia. Bovespa Mais",
    "M2": "Cia. Bovespa Mais Nível 2",
    "MB": "Cia. Balcão Org. Tradicional",
    "DR1": "BDR Nível 1",
    "DR2": "BDR Nível 2",
    "DR3": "BDR Nível 3",
    "DRE": "BDR de ETF",
    "DRN": "BDR Não Patrocinado"
}
