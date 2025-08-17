import os
import sqlite3
from threading import Lock

import pandas as pd
import psutil


class Config:
    def __init__(self):
        # Carrega todas as sub-configurações
        self.paths = self._define_paths()
        self.domain = self._define_domain_config()
        self.scraping = self._define_scraping_config()
        self.selenium = self._define_selenium_config()
        self.requests = self._define_requests_config()
        self.databases = self._define_database_config()
        self.schemas = self._define_schemas()

        # Cria pastas necessárias
        self._ensure_directories()

    def _define_paths(self):
        """Agrupa informações de caminhos e diretórios."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        backend_folder = os.path.join(base_dir, "backend")
        data_folder = os.path.join(backend_folder, "data")
        bin_folder = os.path.join(backend_folder, "bin")
        utils_folder = os.path.join(backend_folder, "utils")
        temp_folder = os.path.join(base_dir, "temp")
        profiles_folder = os.path.join(base_dir, "profiles")

        return {
            "base_dir": base_dir,
            "backend_folder": backend_folder,
            "data_folder": data_folder,
            "bin_folder": bin_folder,
            "utils_folder": utils_folder,
            "temp_folder": temp_folder,
            "profiles_folder": profiles_folder,
        }

    def _ensure_directories(self):
        """Garante que as pastas existam antes de prosseguir."""
        os.makedirs(self.paths["backend_folder"], exist_ok=True)
        os.makedirs(self.paths["data_folder"], exist_ok=True)
        os.makedirs(self.paths["bin_folder"], exist_ok=True)
        os.makedirs(self.paths["utils_folder"], exist_ok=True)
        os.makedirs(self.paths["temp_folder"], exist_ok=True)
        os.makedirs(self.paths["profiles_folder"], exist_ok=True)

        return True

    def _define_database_config(self):
        """Define nomes de bancos, tabelas e respectivos caminhos, além de
        backups para cada BD."""
        # Nomes dos arquivos de BD
        db_raw = "app_raw.db"
        db_ready = "app_ready.db"

        backup_name = "backup"

        data_folder = self.paths["data_folder"]

        # Table Names
        tbl_company_info = "tbl_company_info"
        tbl_nsd = "tbl_nsd"
        tbl_stock_data = "tbl_stock_data"
        tbl_statements_raw = "tbl_statements_raw"
        tbl_pending_companies = "tbl_pending_companies"
        tbl_statements_normalized = "tbl_statements_normalized"
        tbl_statements_corp_events = "tbl_statements_corp_events"

        tbl_statements_ready = "tbl_statements_ready"

        # Index Names
        idx_company_info = "idx_company_info"
        idx_nsd = "idx_nsd"
        idx_stock_data = "idx_stock_data"
        idx_statements_raw = "idx_statements_raw"
        idx_statements_normalized = "idx_statements_normalized"
        idx_statements_corp_events = "idx_statements_corp_events"

        idx_statements_ready = "idx_statements_ready"

        # Monta caminhos
        raw_path = os.path.join(data_folder, db_raw)
        ready_path = os.path.join(data_folder, db_ready)

        # Monta nomes de backup
        backup_raw = f"{db_raw.split('.')[0]}_{backup_name}.{db_raw.split('.')[-1]}"
        backup_ready = f"{db_ready.split('.')[0]}_{backup_name}.{db_ready.split('.')[-1]}"

        # Dicionário final de configurações de BD
        return {
            # Banco RAW: Coleta e Transformação
            "raw": {
                "filename": db_raw,
                "filepath": raw_path,
                "backup_filename": backup_raw,
                "table": {
                    "company_info": tbl_company_info,
                    "nsd": tbl_nsd,
                    "stock_data": tbl_stock_data,
                    "statements_raw": tbl_statements_raw,
                    "pending_companies": tbl_pending_companies, 
                    "statements_normalized": tbl_statements_normalized,
                    "statements_corp_events": tbl_statements_corp_events,
                    "idx_statements_ready": idx_statements_ready,
                    # Caso surjam outras tabelas intermediárias, adicionar aqui
                },
                "index": {
                    "company_info": idx_company_info,
                    "nsd": idx_nsd,
                    "stock_data": idx_stock_data,
                    "statements_raw": idx_statements_raw,
                    "statements_normalized": idx_statements_normalized,
                    "statements_corp_events": idx_statements_corp_events,
                    # Caso surjam outras tabelas intermediárias, adicionar aqui
                },
            },
            # Banco READY: Visualização
            "ready": {
                "filename": db_ready,
                "filepath": ready_path,
                "backup_filename": backup_ready,
                "table": {"statements_ready": tbl_statements_ready},
            },
        }

    def _define_schemas(self):
        """Mapeia cada banco -> cada tabela -> script de criação (CREATE
        TABLE).

        Usa as variáveis definidas em _define_database_config para
        manter consistência.
        """

        # Recupera a config de bancos
        db_config = self.databases

        # Extrai as strings de tabela (para não escrever repetidamente no schema)
        tbl_company_info = db_config["raw"]["table"]["company_info"]  # "company_info"
        tbl_nsd = db_config["raw"]["table"]["nsd"]  # "nsd"
        tbl_stock_data = db_config["raw"]["table"]["stock_data"]  # "stock_data"

        tbl_statements_raw = db_config["raw"]["table"]["statements_raw"]  # "statements_raw"
        tbl_pending_companies = db_config["raw"]["table"]["pending_companies"] # pending_companies

        tbl_statements_normalized = db_config["raw"]["table"]["statements_normalized"]
        tbl_statements_corp_events = db_config["raw"]["table"]["statements_corp_events"]

        tbl_statements_ready = db_config["ready"]["table"]["statements_ready"]  # "statements_ready"

        return {
            # Banco raw
            db_config["raw"]["filename"]: {
                tbl_company_info: f"""
                    CREATE TABLE IF NOT EXISTS {tbl_company_info} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cvm_code TEXT,
                        ticker TEXT,
                        company_name TEXT,
                        trading_name TEXT,
                        market_indicator TEXT,

                        listing TEXT,
                        ticker_codes TEXT,
                        isin_codes TEXT,

                        sector TEXT,
                        subsector TEXT,
                        segment TEXT,
                        activity TEXT,
                        describle_category_bvmf TEXT,
                        segment_eng TEXT,

                        cnpj TEXT,
                        website TEXT,
                        registrar TEXT,
                        main_registrar TEXT,

                        date_listing TEXT,
                        last_date TEXT,
                        date_quotation TEXT,

                        type TEXT,
                        status TEXT,
                        type_bdr TEXT,
                        has_quotation TEXT,
                        has_emissions TEXT,
                        has_bdr TEXT,
                        UNIQUE(company_name)
                    );
                    CREATE INDEX IF NOT EXISTS idx_company_info ON {tbl_company_info} (company_name);
                """,
                tbl_nsd: f"""
                    CREATE TABLE IF NOT EXISTS {tbl_nsd} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nsd INTEGER,
                        company_name TEXT,
                        quarter TEXT,
                        version INTEGER,
                        nsd_type TEXT,
                        dri TEXT,
                        auditor TEXT,
                        responsible_auditor TEXT,
                        protocol TEXT,
                        sent_date TEXT,
                        reason TEXT,
                        UNIQUE(nsd)
                    );
                    CREATE INDEX IF NOT EXISTS idx_nsd ON {tbl_nsd} (nsd);
                """,
                tbl_stock_data: f"""
                    CREATE TABLE IF NOT EXISTS {tbl_stock_data} (
                        company_name TEXT,
                        ticker TEXT,
                        ticker_code TEXT,
                        date TEXT,
                        close REAL,
                        dividends REAL,
                        high REAL,
                        low REAL,
                        open REAL,
                        stock_splits INTEGER,
                        volume INTEGER,
                        PRIMARY KEY (company_name, ticker_code, date)
                    );
                    CREATE INDEX IF NOT EXISTS idx_stock_data ON {tbl_stock_data} (company_name, ticker_code, date);
                """,
                tbl_statements_raw: f"""
                    CREATE TABLE IF NOT EXISTS {tbl_statements_raw} (
                        nsd INTEGER,
                        sector TEXT,
                        subsector TEXT,
                        segment TEXT,
                        company_name TEXT,
                        quarter TEXT,
                        version TEXT,
                        type TEXT,
                        frame TEXT,
                        account TEXT,
                        description TEXT,
                        value REAL,
                        processed TEXT DEFAULT NULL, 
                        PRIMARY KEY (company_name, quarter, version, type, frame, account, description)
                    );
                        CREATE INDEX IF NOT EXISTS idx_statements_raw_composite 
                            ON {tbl_statements_raw} (company_name, quarter, version, type, frame, account, description);
                        CREATE INDEX IF NOT EXISTS idx_statements_raw_nsd 
                            ON {tbl_statements_raw} (nsd);
                """,
                tbl_pending_companies: f"""
                    CREATE TABLE IF NOT EXISTS {tbl_pending_companies} (
                        company_name TEXT PRIMARY KEY
                    );
                    CREATE INDEX IF NOT EXISTS idx_{tbl_pending_companies}
                        ON {tbl_pending_companies}(company_name);

                    -- Triggers existentes…
                    CREATE TRIGGER IF NOT EXISTS trg_after_insert_statements
                    AFTER INSERT ON {tbl_statements_raw}
                    WHEN NEW.processed IS NULL OR NEW.processed <> NEW.version
                    BEGIN
                        INSERT OR IGNORE INTO {tbl_pending_companies}(company_name)
                        VALUES (NEW.company_name);
                    END;

                    CREATE TRIGGER IF NOT EXISTS trg_after_update_statements_remove
                    AFTER UPDATE OF processed,version ON {tbl_statements_raw}
                    WHEN (OLD.processed IS NULL OR OLD.processed <> OLD.version)
                    AND NOT (NEW.processed IS NULL OR NEW.processed <> NEW.version)
                    BEGIN
                        DELETE FROM {tbl_pending_companies}
                        WHERE company_name = NEW.company_name
                        AND NOT EXISTS (
                            SELECT 1 FROM {tbl_statements_raw} AS t2
                            WHERE t2.company_name = NEW.company_name
                            AND (t2.processed IS NULL OR t2.processed <> t2.version)
                        );
                    END;

                    CREATE TRIGGER IF NOT EXISTS trg_after_update_statements_add
                    AFTER UPDATE OF processed,version ON {tbl_statements_raw}
                    WHEN NOT (OLD.processed IS NULL OR OLD.processed <> OLD.version)
                    AND  (NEW.processed IS NULL OR NEW.processed <> NEW.version)
                    BEGIN
                        INSERT OR IGNORE INTO {tbl_pending_companies}(company_name)
                        VALUES (NEW.company_name);
                    END;

                    -- Popula na primeira inicialização
                    INSERT OR IGNORE INTO {tbl_pending_companies}(company_name)
                    SELECT DISTINCT company_name
                    FROM {tbl_statements_raw}
                    WHERE processed IS NULL OR processed <> version;
                """, 
                tbl_statements_normalized: f"""
                    CREATE TABLE IF NOT EXISTS {tbl_statements_normalized} (
                        nsd INTEGER,
                        sector TEXT,
                        subsector TEXT,
                        segment TEXT,
                        company_name TEXT,
                        quarter TEXT,
                        version TEXT,
                        type TEXT,
                        frame TEXT,
                        account TEXT,
                        description TEXT,
                        value REAL,
                        original_value REAL,
                        PRIMARY KEY (company_name, quarter, version, type, frame, account, description)
                    );

                    CREATE INDEX IF NOT EXISTS idx_statements_normalized ON {tbl_statements_normalized} (company_name, quarter, version, type, frame, account, description);
                """,
                tbl_statements_corp_events: f"""
                    CREATE TABLE IF NOT EXISTS {tbl_statements_corp_events} (
                        ticker_code TEXT,
                        group_type TEXT,
                        date TEXT,
                        close REAL,
                        dividends REAL,
                        high REAL,
                        low REAL,
                        open REAL,
                        stock_splits REAL,
                        volume INTEGER,
                        nsd INTEGER,
                        sector TEXT,
                        subsector TEXT,
                        segment TEXT,
                        company_name TEXT,
                        quarter TEXT,
                        version TEXT,
                        PRIMARY KEY (company_name, quarter, version, date, group_type)
                    );
                    CREATE INDEX IF NOT EXISTS idx_statements_corp_events ON {tbl_statements_corp_events} (company_name, quarter, version, date, group_type);
                """,
            },
            # Banco ready
            db_config["ready"]["filename"]: {
                tbl_statements_ready: f"""
                    CREATE TABLE IF NOT EXISTS {tbl_statements_ready} (
                        nsd INTEGER,
                        sector TEXT,
                        subsector TEXT,
                        segment TEXT,
                        company_name TEXT,
                        quarter TEXT,
                        version TEXT,
                        type TEXT,
                        frame TEXT,
                        account TEXT,
                        description TEXT,
                        value REAL,
                        PRIMARY KEY (company_name, quarter, version, type, frame, account, description)
                    );
                    CREATE INDEX IF NOT EXISTS idx_statements_ready ON {tbl_statements_ready} (company_name, quarter, version, type, frame, account, description);
                """
            },
        }

    def _find_heaviest_table(self, db_filepath, sample_size=10_000):
        """Encontra a tabela com linhas mais pesadas para basear o
        chunk_size."""
        heaviest_table = None
        max_memory_per_row = 1  # fallback seguro

        try:
            with sqlite3.connect(db_filepath) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]

                for table in tables:
                    try:
                        df_sample = pd.read_sql_query(f"SELECT * FROM {table} LIMIT ?", conn, params=(sample_size,))
                        if len(df_sample) > 0:
                            memory_per_row = df_sample.memory_usage(deep=True).sum() / len(df_sample)
                            if memory_per_row > max_memory_per_row:
                                max_memory_per_row = memory_per_row
                                heaviest_table = table
                    except Exception:
                        continue  # ignora erros de leitura de tabela

        except Exception as e:
            self.log_error(f"Erro ao encontrar tabela mais pesada: {e}")

        return heaviest_table, max_memory_per_row

    def _define_scraping_config(self):
        """Configurações gerais de scraping e processamento em lote."""
        cpu = os.cpu_count() or 1
        batch_size = cpu * 10
        max_workers = cpu * 1
        stock_data_start_date = "1960-01-01"
        update_days = 2

        # Database configuration
        databases = self._define_database_config()
        raw_path = databases["raw"]["filepath"]

        # Inicializa
        sample_size = 10_000
        memory_per_row = 1
        db_lock = Lock()

        with db_lock:
            try:
                heaviest_table, memory_per_row = self._find_heaviest_table(raw_path, sample_size)

                if memory_per_row <= 0:
                    memory_per_row = 1  # proteção para divisões

                memory_total = psutil.virtual_memory().total
                memory_available = psutil.virtual_memory().available
                memory_budget = memory_available * 0.5  # usar 50% da memória disponível

                chunk_size = int(memory_budget / memory_per_row)

            except Exception as e:
                self.log_error(f"Erro na definição de chunk_size dinâmico: {e}")
                chunk_size = sample_size

        return {
            "batch_size": batch_size,
            "max_workers": max_workers,
            "chunk_size": chunk_size,
            "stock_data_start_date": stock_data_start_date,
            "update_days": update_days,
        }

    def _define_selenium_config(self):
        """Configurações específicas do Selenium."""
        wait_time = 2
        max_retries = 5
        log_loop = 50

        registry_paths = [
            r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
            r'reg query "HKEY_LOCAL_MACHINE\Software\Google\Chrome\BLBeacon" /v version',
            r'reg query "HKEY_LOCAL_MACHINE\Software\WOW6432Node\Google\Chrome\BLBeacon" /v version',
        ]
        chrome_path_64 = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        chrome_path_32 = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

        computer_name = os.environ["COMPUTERNAME"]
        chromedriver_path = os.path.join(self.paths["bin_folder"], "chromedriver-win64", "chromedriver.exe")

        proxy_socks5 = ""  # "127.0.0.1:9050"  # deixe "" ou None para desativar

        return {
            "wait_time": wait_time,
            "max_retries": max_retries,
            "log_loop": log_loop, 
            "driver": None,
            "driver_wait": None,
            "registry_paths": registry_paths,
            "chrome_path_64": chrome_path_64,
            "chrome_path_32": chrome_path_32,
            "computer_name": computer_name,
            "chromedriver_path": chromedriver_path,
            "proxy_socks5": proxy_socks5,
        }

    def _define_requests_config(self):
        """Configurações de headers, user-agents, referers etc."""
        user_agents = [
            # Chrome (Windows, macOS, Linux, Android)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
            "Mozilla/5.0 (Android 13; Mobile; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Mobile Safari/537.36",
            # Firefox (Windows, macOS, Linux, Android)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_1; rv:115.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (Android 13; Mobile; SM-S908B; rv:115.0) Gecko/115.0 Firefox/115.0",
            # Safari (macOS, iOS)
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            # Microsoft Edge (Windows, macOS)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Edg/114.0.1823.82",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Edg/114.0.1823.82",
            # Brave (Windows, macOS, Linux)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Brave/1.57.57",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Brave/1.57.57",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Brave/1.57.57",
            # Opera (Windows, macOS)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 OPR/99.0.4788.88",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 OPR/99.0.4788.88",
            # Samsung Internet (Android)
            "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/22.0 Chrome/114.0.5735.199 Mobile Safari/537.36",
            # Vivaldi Browser (Desktop and Android)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Vivaldi/6.1.3035.111",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Vivaldi/6.1.3035.111",
            "Mozilla/5.0 (Android 13; Mobile; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Vivaldi/6.1.3035.111",
            # Yandex Browser (Russia and CIS)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 YaBrowser/23.7.3.652 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 YaBrowser/23.7.3.652 Safari/537.36",
            "Mozilla/5.0 (Android 13; Mobile; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 YaBrowser/23.7.3.652 Mobile Safari/537.36",
            # Xbox and PlayStation Browsers
            "Mozilla/5.0 (Xbox; U; Windows NT 10.0; WOW64; en-US) AppleWebKit/537.36 (KHTML, like Gecko) Edge/44.18363.8131",
            "Mozilla/5.0 (PlayStation 5; AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
            # Samsung Galaxy Tablet (Android)
            "Mozilla/5.0 (Linux; Android 13; SM-T970) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
            # Googlebot Mobile and Desktop (SEO Testing)
            "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Mobile Safari/537.36 Googlebot/2.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36 Googlebot/2.1",
        ]

        referers = [
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://www.duckduckgo.com/",
            "https://www.facebook.com/",
            "https://twitter.com/",
            "https://www.reddit.com/",
            "https://www.youtube.com/",
            "https://www.linkedin.com/",
            "https://www.instagram.com/",
            "https://www.tiktok.com/",
            "https://www.wikipedia.org/",
            "https://www.amazon.com/",
            "https://www.ebay.com/",
            "https://www.alibaba.com/",
            "https://www.github.com/",
            "https://stackoverflow.com/",
            "https://www.quora.com/",
            "https://news.ycombinator.com/",
            "https://www.netflix.com/",
            "https://www.twitch.tv/",
            "https://www.spotify.com/",
            "https://www.medium.com/",
            "https://www.dropbox.com/",
            "https://www.paypal.com/",
            "https://www.apple.com/",
            "https://www.microsoft.com/",
            "https://www.adobe.com/",
        ]

        languages = [
            "en-US;q=1.0",  # English (United States)
            "en-GB;q=0.9",  # English (United Kingdom)
            "es-ES;q=0.9",  # Spanish (Spain)
            "es-MX;q=0.8",  # Spanish (Mexico)
            "fr-FR;q=0.9",  # French (France)
            "de-DE;q=0.9",  # German (Germany)
            "it-IT;q=0.8",  # Italian (Italy)
            "pt-BR;q=0.9",  # Portuguese (Brazil)
            "pt-PT;q=0.8",  # Portuguese (Portugal)
            "ja-JP;q=0.8",  # Japanese
            "zh-CN;q=0.8",  # Chinese (Simplified)
            "zh-TW;q=0.7",  # Chinese (Traditional)
            "ko-KR;q=0.8",  # Korean
            "ru-RU;q=0.9",  # Russian
            "ar-SA;q=0.8",  # Arabic (Saudi Arabia)
            "hi-IN;q=0.8",  # Hindi (India)
            "tr-TR;q=0.8",  # Turkish
            "nl-NL;q=0.8",  # Dutch (Netherlands)
            "sv-SE;q=0.8",  # Swedish (Sweden)
            "pl-PL;q=0.8",  # Polish
            "da-DK;q=0.8",  # Danish (Denmark)
            "no-NO;q=0.8",  # Norwegian
            "cs-CZ;q=0.8",  # Czech (Czech Republic)
            "el-GR;q=0.8",  # Greek
            "th-TH;q=0.8",  # Thai
            "id-ID;q=0.8",  # Indonesian
        ]

        return {"user_agents": user_agents, "referers": referers, "languages": languages}

    def _define_domain_config(self):
        """Aqui adicionamos tudo que for específico da sua lógica de negócios:

        - strings de formatação (sep_dash, sep_pipe)
        - prefixos 'stock_prefix'
        - nomes de colunas de tabelas específicas
        - urls para scraping B3
        - definições de statements / infos de NSD
        - etc.
        """

        # Strings de formatação
        sep_dash = " - "
        sep_pipe = " | "
        stock_prefix = "00."
        indent = " " * 2

        # URLs de scraping B3
        companies_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/search?language=pt-br"
        company_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/?language=pt-br"

        endpoints_config = {
            # Dados da Empresa
            ('Dados da Empresa', 'Composição do Capital'): {"Informacao": None, "Demonstracao": None, "Periodo": 0},

            # DFs Individuais
            ('DFs Individuais', 'Balanço Patrimonial Ativo'): {"Informacao": 1, "Demonstracao": 2, "Periodo": 0},
            ('DFs Individuais', 'Balanço Patrimonial Passivo'): {"Informacao": 1, "Demonstracao": 3, "Periodo": 0},
            ('DFs Individuais', 'Demonstração do Resultado'): {"Informacao": 1, "Demonstracao": 4, "Periodo": 0},
            ('DFs Individuais', 'Demonstração do Resultado Abrangente'): {"Informacao": 1, "Demonstracao": 5, "Periodo": 0},
            ('DFs Individuais', 'Demonstração do Fluxo de Caixa'): {"Informacao": 1, "Demonstracao": 99, "Periodo": 0},
            ('DFs Individuais', 'Demonstração de Valor Adicionado'): {"Informacao": 1, "Demonstracao": 9, "Periodo": 0},

            # DFs Consolidadas
            ('DFs Consolidadas', 'Balanço Patrimonial Ativo'): {"Informacao": 2, "Demonstracao": 2, "Periodo": 0},
            ('DFs Consolidadas', 'Balanço Patrimonial Passivo'): {"Informacao": 2, "Demonstracao": 3, "Periodo": 0},
            ('DFs Consolidadas', 'Demonstração do Resultado'): {"Informacao": 2, "Demonstracao": 4, "Periodo": 0},
            ('DFs Consolidadas', 'Demonstração do Resultado Abrangente'): {"Informacao": 2, "Demonstracao": 5, "Periodo": 0},
            ('DFs Consolidadas', 'Demonstração do Fluxo de Caixa'): {"Informacao": 2, "Demonstracao": 99, "Periodo": 0},
            ('DFs Consolidadas', 'Demonstração de Valor Adicionado'): {"Informacao": 2, "Demonstracao": 9, "Periodo": 0},
        }




        # Colunas colunas de "company_info"
        columns_company_info = [
            "cvm_code",
            "company_name",
            "ticker",
            "ticker_codes",
            "isin_codes",
            "trading_name",
            "sector",
            "subsector",
            "segment",
            "listing",
            "activity",
            "registrar",
            "cnpj",
            "website",
        ] 

        web_company_columns_mapping = {
            "codeCVM": "cvm_code",
            "issuingCompany": "ticker",
            "companyName": "company_name",
            "tradingName": "trading_name",
            "market": "listing",
            "ticker_codes": "ticker_codes",
            "isin_codes": "isin_codes",
            "sector": "sector",
            "subsector": "subsector",
            "segment": "segment",
            "segmentEng": "segment_eng",
            "activity": "activity",
            "describle_category_bvmf": "describle_category_bvmf",
            "last_date": "last_date",
            "dateListing": "date_listing",
            "date_quotation": "date_quotation",
            "cnpj": "cnpj",
            "website": "website",
            "registrar": "registrar",
            "main_registrar": "main_registrar",
            "status": "status",
            "type": "type",
            "marketIndicator": "market_indicator",
            "typeBDR": "type_bdr",
            "has_quotation": "has_quotation",
            "has_emissions": "has_emissions",
            "has_bdr": "has_bdr",
        }

        # NSD scraping settings
        columns_nsd = [
            "nsd",
            "company_name",
            "quarter",
            "version",
            "nsd_type",
            "dri",
            "auditor",
            "responsible_auditor",
            "protocol",
            "sent_date",
            "reason",
        ]
        sort_order_nsd = ["company_name", "quarter", "version"]
        default_daily_submission_estimate = 30
        safety_factor = 3

        # Configurações para statements
        statements_version_delimiter = [
            "company_name",
            "quarter",
            "type",
            # "version",
            "frame",
            "account",
            "description",
        ]

        statements_sheet_columns = ["company_name", "quarter", "version", "type", "frame"]

        statements_types = ["DEMONSTRACOES FINANCEIRAS PADRONIZADAS", "INFORMACOES TRIMESTRAIS"]
        statements_columns_empty_df = [
            "date",
            "nsd",
            "sector",
            "subsector",
            "segment",
            "company_name",
            "quarter",
            "version",
        ]
        financial_statements_columns = ["account", "description", "value"]
        statements_columns = [
            "nsd",
            "sector",
            "subsector",
            "segment",
            "company_name",
            "quarter",
            "version",
            "type",
            "frame",
            "account",
            "description",
            "value",
        ]
        statements_order = [
            "sector",
            "subsector",
            "segment",
            "company_name",
            "quarter",
            "account",
            "description",
            "type",
        ]

        accounts_year_end = ["3", "4"]
        accounts_cumulative_quarter = ["6", "7"]

        # Dados de mercado (historical/stock)
        historical_stock_data_columns = ["date", "close", "high", "low", "open", "volume", "stock_splits", "dividends"]
        historical_stock_data_all_columns = ["company_name", "ticker", "ticker_code"] + historical_stock_data_columns

        # Dados “standard”
        statements_index_columns = ["nsd", "sector", "subsector", "segment", "company_name", "quarter", "version"]
        statements_pivot_columns = ["account", "description", "frame", "type"]

        # splits
        split_columns = ["company_name", "ticker", "ticker_code", "date", "stock_splits"]

        # Descrições & contas
        descriptions = {
            "acoes_on": "Ações ON Ordinárias",
            "acoes_pn": "Ações PN Preferenciais",
            "acoes_on_tesouraria": "Em Tesouraria Ações ON Ordinárias",
            "acoes_pn_tesouraria": "Em Tesouraria Ações PN Preferenciais",
        }
        accounts = {
            "acoes_on": "00.01.01",
            "acoes_pn": "00.01.02",
            "acoes_on_tesouraria": "00.02.01",
            "acoes_pn_tesouraria": "00.02.02",
        }

        # Financial and Capital statements
        statements_financial_data = [
            ["DFs Consolidadas", "Demonstração do Resultado"],
            ["DFs Consolidadas", "Balanço Patrimonial Ativo"],
            ["DFs Consolidadas", "Balanço Patrimonial Passivo"],
            ["DFs Consolidadas", "Demonstração do Fluxo de Caixa"],
            ["DFs Consolidadas", "Demonstração de Valor Adicionado"],
            ["DFs Individuais", "Demonstração do Resultado"],
            ["DFs Individuais", "Balanço Patrimonial Ativo"],
            ["DFs Individuais", "Balanço Patrimonial Passivo"],
            ["DFs Individuais", "Demonstração do Fluxo de Caixa"],
            ["DFs Individuais", "Demonstração de Valor Adicionado"],
        ]
        statements_capital_config = [["Dados da Empresa", "Composição do Capital"]]

        # Judicial terms to remove
        words_to_remove = [
            "  EM LIQUIDACAO",
            " EM LIQUIDACAO",
            " EXTRAJUDICIAL",
            "  EM RECUPERACAO JUDICIAL",
            "  EM REC JUDICIAL",
            " EM RECUPERACAO JUDICIAL",
            " EM LIQUIDACAO EXTRAJUDICIAL",
            " EMPRESA FALIDA",
        ]

        # Governance levels
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
            "DRN": "BDR Não Patrocinado",
        }

        # Tipos de ações
        tipos_acoes = {
            "1": "Direitos de Subscrição de Ações Ordinárias",
            "2": "Direitos de Subscrição de Ações Preferenciais",
            "3": "Ações Ordinárias (ON)",
            "4": "Ações Preferenciais (PN)",
            "5": "Ações Preferenciais Classe A (PNA)",
            "6": "Ações Preferenciais Classe B (PNB)",
            "7": "Ações Preferenciais Classe C (PNC)",
            "8": "Ações Preferenciais Classe D (PND)",
            "9": "Recibos de Subscrição",
            "10": "BDRs – Brazilian Depositary Receipts",
            "11": "Units (Conjunto de ações ordinárias e preferenciais)",
            "12": "Cotas de Fundos de Investimento Imobiliário (FII)",
            "31": "Direitos de Subscrição de Units",
            "32": "Direitos de Subscrição de BDRs",
            "33": "Recibos de Subscrição de Units",
            "34": "Recibos de Subscrição de BDRs",
            "35": "Recibos de Subscrição de FIIs",
            "39": "Recibos de Subscrição de Outros Valores Mobiliários",
            "41": "Certificados de Depósito de Valores Mobiliários (CVM)",
            "42": "Certificados de Investimento",
            "43": "Cotas de Índices de Ações (ETFs)",
            "44": "Recibos de Subscrição de ETFs",
            "45": "Cotas de Fundos de Índices Estrangeiros (ETFs BDR)",
            "46": "Direitos de Subscrição de Fundos de Índices",
            "47": "Cotas de Fundos de Participação",
            "49": "Cotas de Fundos de Índices (Outros)",
            "50": "Outros Valores Mobiliários",
            "51": "Debêntures Simples",
            "52": "Debêntures Conversíveis",
            "56": "Cotas de Fundos de Investimento em Participações (FIP)",
            "57": "Cotas de Fundos de Investimento em Direitos Creditórios (FIDC)",
            "58": "Cotas de Fundos de Investimento em Ações (FIA)",
            "59": "Cotas de Fundos de Investimento Multimercado",
            "60": "Certificados de Recebíveis Imobiliários (CRI)",
            "61": "Certificados de Recebíveis do Agronegócio (CRA)",
            "62": "Notas Promissórias",
            "63": "Commercial Papers",
            "64": "Cotas de Fundos de Investimento em Ações Estruturadas",
            "66": "Cotas de Fundos de Investimento em Infraestrutura (FIP-IE)",
            "67": "Cotas de Fundos de Investimento em Participação Multiestratégia (FIP-ME)",
            "68": "Cotas de Fundos de Investimento em Participação de Inovação (FIP-PD&I)",
            "71": "Certificados de Operações Estruturadas (COE)",
            "81": "Certificados de Crédito Bancário (CCB)",
            "82": "Letra Financeira (LF)",
            "83": "Letra de Câmbio (LC)",
            "84": "Letra de Crédito Imobiliário (LCI)",
            "85": "Letra de Crédito do Agronegócio (LCA)",
            "86": "Cédula de Crédito Bancário (CCB)",
            "87": "Cédula de Produto Rural (CPR)",
            "88": "Letra Imobiliária Garantida (LIG)",
            "89": "Cotas de Fundos de Investimento em Crédito Privado",
            "90": "Títulos Públicos Federais (Tesouro Direto)",
            "91": "Cotas de Fundos de Investimento em Previdência",
        }

        # Map de tipos de ações
        stock_type_map = {
            "OR": {"code": "3", "description": "Ações Ordinárias (ON)"},
            "PR": {"code": "4", "description": "Ações Preferenciais (PN)"},
            "PA": {"code": "5", "description": "Ações Preferenciais Classe A (PNA)"},
            "PB": {"code": "6", "description": "Ações Preferenciais Classe B (PNB)"},
            "PC": {"code": "7", "description": "Ações Preferenciais Classe C (PNC)"},
            "PD": {"code": "8", "description": "Ações Preferenciais Classe D (PND)"},
            "RS": {"code": "9", "description": "Recibos de Subscrição"},
        }

        return {
            "sep_dash": sep_dash,
            "sep_pipe": sep_pipe,
            "stock_prefix": stock_prefix,
            "indent": indent,
            "companies_url": companies_url,
            "company_url": company_url,
            "endpoints_config": endpoints_config, 
            "columns_company_info": columns_company_info,
            "web_company_columns_mapping": web_company_columns_mapping, 
            "columns_nsd": columns_nsd,
            "sort_order_nsd": sort_order_nsd,
            "default_daily_submission_estimate": default_daily_submission_estimate,
            "safety_factor": safety_factor,
            "statements_version_delimiter": statements_version_delimiter,
            "statements_sheet_columns": statements_sheet_columns,
            "statements_types": statements_types,
            "statements_columns_empty_df": statements_columns_empty_df,
            "financial_statements_columns": financial_statements_columns,
            "statements_columns": statements_columns,
            "statements_order": statements_order,
            "accounts_year_end": accounts_year_end,
            "accounts_cumulative_quarter": accounts_cumulative_quarter,
            "historical_stock_data_columns": historical_stock_data_columns,
            "historical_stock_data_all_columns": historical_stock_data_all_columns,
            "statements_index_columns": statements_index_columns,
            "statements_pivot_columns": statements_pivot_columns,
            "split_columns": split_columns,
            "descriptions": descriptions,
            "accounts": accounts,
            "statements_financial_data": statements_financial_data,
            "statements_capital_config": statements_capital_config,
            "words_to_remove": words_to_remove,
            "governance_levels": governance_levels,
            "tipos_acoes": tipos_acoes,
            "stock_type_map": stock_type_map,
        }
