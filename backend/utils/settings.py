# System-wide settings
db_name = 'b3.db'  # Database name
db_folder = 'backend/data'
db_folder_short = 'data'
db_path = 'backend/data/b3.db'
backup_name = 'backup'

# batches
batch_size = 50  # Batch size for data processing
max_workers = 8
big_batch_size = int(40000 / max_workers)

# Selenium settings
wait_time = 2  # Wait time for Selenium operations
driver = driver_wait = None  # Placeholders for Selenium driver and wait objects

# Requests
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 5.1; rv:36.0) Gecko/20100101 Firefox/36.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/83.0.478.37",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 13_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/53.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134"
]
REFERERS = [
    'https://www.google.com/',
    'https://www.bing.com/',
    'https://www.yahoo.com/',
    'https://www.facebook.com/',
    'https://twitter.com/',
    'https://www.reddit.com/',
    'https://www.youtube.com/',
    'https://www.linkedin.com/',
    'https://www.instagram.com/',
    'https://www.pinterest.com/',
    'https://www.wikipedia.org/',
    'https://www.amazon.com/',
    'https://www.ebay.com/',
    'https://www.craigslist.org/',
    'https://www.github.com/',
    'https://stackoverflow.com/',
    'https://www.quora.com/',
    'https://news.ycombinator.com/',
    'https://www.netflix.com/',
    'https://www.twitch.tv/',
    'https://www.spotify.com/',
    'https://www.tumblr.com/',
    'https://www.medium.com/',
    'https://www.dropbox.com/',
    'https://www.paypal.com/'
]
LANGUAGES = ['en-US;q=1.0', 'es-ES;q=0.9', 'fr-FR;q=0.8', 'de-DE;q=0.7', 'it-IT;q=0.6', 'pt-BR;q=0.9', 'ja-JP;q=0.8', 'zh-CN;q=0.7', 'ko-KR;q=0.6', 'ru-RU;q=0.9', 'ar-SA;q=0.8', 'hi-IN;q=0.7', 'tr-TR;q=0.6', 'nl-NL;q=0.9', 'sv-SE;q=0.8', 'pl-PL;q=0.7', 'fi-FI;q=0.6', 'da-DK;q=0.9', 'no-NO;q=0.8', 'hu-HU;q=0.7', 'ro-RO;q=0.6', 'cs-CZ;q=0.9', 'el-GR;q=0.8', 'th-TH;q=0.7', 'id-ID;q=0.6']

# Company Info from B3
companies_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/search?language=pt-br"  # URL for the B3 companies search page
company_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/?language=pt-br"  # URL for the B3 company detail page
company_table = 'company_info'
company_columns = ['cvm_code', 'company_name', 'ticker', 'ticker_codes', 'isin_codes', 'trading_name', 'sector', 'subsector', 'segment', 'listing', 'activity', 'registrar', 'cnpj', 'website']

# NSD scraping settings
nsd_columns = ['nsd', 'company_name', 'quarter', 'version', 'nsd_type', 'auditor', 'responsible_auditor', 'protocol', 'sent_date', 'reason']  # Adjusted columns based on NSD data
nsd_order = ['company_name', 'quarter', 'version']
default_daily_submission_estimate = 30
safety_factor = 3  # Apply a safety factor to account for possible increases

# Statements settings
statements_sheet_columns = ['company_name', 'quarter', 'version', 'type', 'frame']

statements_file = 'statements'
statements_types = ["DEMONSTRACOES FINANCEIRAS PADRONIZADAS", "INFORMACOES TRIMESTRAIS"]
financial_statements_columns = ['account', 'description', 'value']  # Assuming these are the financial/statements columns
statements_columns = ['nsd', 'sector', 'subsector', 'segment', 'company_name', 'quarter', 'version', 'type', 'frame'] + financial_statements_columns
statements_order = ['sector', 'subsector', 'segment', 'company_name', 'quarter', 'version', 'type', 'account', 'description']
year_end_accounts = ['3', '4']
cumulative_quarter_accounts = ['6', '7']

# Math settings
statements_file_math = 'math'

# Standard settings
statements_standard = 'standard'

# Descriptions and accounts
descriptions = {
    'acoes_on': 'Ações ON Ordinárias',
    'acoes_pn': 'Ações PN Preferenciais',
    'acoes_on_tesouraria': 'Em Tesouraria Ações ON Ordinárias',
    'acoes_pn_tesouraria': 'Em Tesouraria Ações PN Preferenciais'
}

accounts = {
    'acoes_on': '00.01.01',
    'acoes_pn': '00.01.02',
    'acoes_on_tesouraria': '00.02.01',
    'acoes_pn_tesouraria': '00.02.02'
}



# Financial and Capital Statements from b3 website
financial_data_statements = [
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

# Capital data configurations
statements_data_statements = [
    ['Dados da Empresa', 'Composição do Capital'], 
]

# List of judicial terms to be removed from company names
words_to_remove = [
    '  EM LIQUIDACAO', ' EM LIQUIDACAO', ' EXTRAJUDICIAL', 
    '  EM RECUPERACAO JUDICIAL', '  EM REC JUDICIAL', 
    ' EM RECUPERACAO JUDICIAL', ' EM LIQUIDACAO EXTRAJUDICIAL', ' EMPRESA FALIDA', 
]

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

