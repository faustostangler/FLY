import datetime
import time
from io import StringIO
from threading import Lock
import os
import re

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlencode, quote_plus
from utils.base_processor import BaseProcessor
from bs4 import BeautifulSoup


class StatementsProcessor(BaseProcessor):
    """Financial Statements."""

    def __init__(self):
        super().__init__()
        self.db_lock = Lock()  # Initialize a threading Lock

        # Define at the beginning of your script
        self.total_block_time = 0
        
        # track total bytes transferred (in bytes)
        self.shared_total_bytes = None  # dicionário { "total": int, "threads": {thread_id: subtotal} }
        self.total_bytes_transferred = 0  # fallback local counter (for single-thread usage)
        self.shared_lock = None
        self.thread_id = None  # cada processor deve saber seu thread_id

        self.homepage_url = "https://www.google.com.br"

        # Initialize database and table names
        self.tbl_company = self.config.databases["raw"]["table"]["company_info"]
        self.tbl_nsd = self.config.databases["raw"]["table"]["nsd"]
        self.tbl_statements_raw = self.config.databases["raw"]["table"]["statements_raw"]
        self.db_filepath = self.config.databases["raw"]["filepath"]
        self.database_name = os.path.basename(self.db_filepath)

        # # Initialize driver and other resources
        # self.driver, self.driver_wait = self._initialize_driver()

    def process_instance(self, sub_batch, payload, verbose, progress):
        """Process a single batch by delegating to process_batch."""
        result = pd.DataFrame()  # Return an empty DataFrame on failure

        try:
            print(
                f"Starting batch {progress['batch_index']+1}/{progress['total_batches']} "
                f"{100 * (progress['batch_index']+1) / progress['total_batches']:.02f}%"
            )
            batch_processor = StatementsProcessor()

            # Inject shared control
            batch_processor.shared_total_bytes = self.shared_total_bytes
            batch_processor.shared_lock = self.shared_lock
            batch_processor.thread_id = progress["thread_id"]  # <- inject thread_id

            # Delegate to process_batch for the actual batch processing
            result, benchmark_results = batch_processor.benchmark_function(
                batch_processor.process_batch, sub_batch, payload, verbose, progress, benchmark_mode=False
            )

            # Show subtotal download size
            if self.shared_total_bytes and self.shared_lock and progress.get("thread_id") is not None:
                with self.shared_lock:
                    subtotal = self.shared_total_bytes["threads"].get(progress["thread_id"], 0)
                    print(f"Worker {progress['thread_id']} download: {self._format_bytes(subtotal)}")

            # Save result to database
            self.save_to_db(dataframe=result, table_name=self.tbl_statements_raw, db_filepath=self.db_filepath, alert=False)

        except Exception as e:
            self.log_error(f"Error in process_instance: {e}")

        return result

    @BaseProcessor().profile_generator()
    def process_batch(self, sub_batch, payload, verbose, progress):
        """Process a batch of financial data by iterating over rows and
        scraping statements."""
        try:
            result = []

            start_time = time.monotonic()

            # Initialize batch size tracking
            if self.shared_total_bytes and self.shared_lock and self.thread_id is not None:
                batch_start_bytes = self.shared_total_bytes["threads"].get(self.thread_id, 0)
            else:
                batch_start_bytes = self.total_bytes_transferred

            # create first scraper
            scraper = self._init_scraper(url=self.homepage_url)

            endpoints_config = self.config.domain['endpoints_config']

            for i, (_, row) in enumerate(sub_batch.iterrows()):
                try:
                    # Extract and process data for each row
                    quarter_dfs = self._process_company_quarter_data(row, endpoints_config, scraper)
                    result.append(quarter_dfs)

                    # Track bytes transferred after this ticker
                    if self.shared_total_bytes and self.shared_lock and self.thread_id is not None:
                        bytes_after = self.shared_total_bytes["threads"].get(self.thread_id, 0)
                    else:
                        bytes_after = self.total_bytes_transferred
                    bytes_this_item = bytes_after - batch_start_bytes
                    formatted_size = self._format_bytes(bytes_this_item)
                    batch_start_bytes = bytes_after  # Update for next item

                    batch = 1 # self.config.selenium['log_loop']
                    if i % batch == 0 or i == len(sub_batch) - 1:  # Always log last item too
                    #     # Log progress
                        actual_item = progress["batch_start"] + i + 1 
                        total_items = progress["scrape_size"] + 0
                        worker_info = f"Worker {progress['thread_id']} {100 * actual_item / total_items:.02f}% ({actual_item+0}/{total_items})"
                        nsd = row["nsd"]
                        cvm_code = row['cvm_code']
                        version = ''.join(filter(str.isdigit, str(row['version'])))
                        company_name = row.get("company_name", "")
                        quarter = row.get("quarter").strftime("%Y-%m") if row.get("quarter") else ""
                        sent_date = row.get("sent_date").strftime("%Y-%m-%d %H:%M:%S") if row.get("sent_date") else ""
                        extra_info = [
                            worker_info,
                            sent_date,
                            nsd,
                            company_name,
                            quarter,
                            version, 
                            nsd, 
                            f"({formatted_size})", 
                        ]
                        self.print_info(i, len(sub_batch), start_time, extra_info, indent_level=1)

                        # Save result to database
                        if result:
                            temp_df = pd.concat(result, ignore_index=True)
                        else:
                            columns, dtypes, primary_keys = self._get_table_structure(self.tbl_statements_raw, self.db_filepath)
                            temp_df = pd.DataFrame(columns=columns)

                        self.save_to_db(dataframe=temp_df, table_name=self.tbl_statements_raw, db_filepath=self.db_filepath, alert=False)

                except Exception as e:
                    self.log_error(f"Error processing row {i}: {e}")
                    quarter_data = "empty"

            # After processing the batch
            progress["batch_start"] += len(sub_batch)

            # Combine results into a single DataFrame
            if result:
                result = pd.concat(result, ignore_index=True)
            else:
                result = pd.DataFrame(columns=self.config.domain["statements_columns"])

        except Exception as e:
            self.log_error(e)
        
        return result

    def build_urls(self, row, endpoints_config, hash_value):
        '''
        Build financial statement URLs for a given row using endpoints_config and a provided hash_value.
        Return a list of dictionaries.
        '''
        try:
            urls = []

            # NomeTipoDocumento + CodTipoDocumento
            nsd_type_map = {
                "INFORMACOES TRIMESTRAIS": ("ITR", 3),
                "DEMONSTRACOES FINANCEIRAS PADRONIZADAS": ("DFP", 4)
            }
            nome_tipo_documento, cod_tipo_documento = nsd_type_map.get(row['nsd_type'], ("ITR", 3))

            # Dynamic fields
            nsd = row['nsd']
            cvm_code = row['cvm_code']
            empresa = row['company_name']
            data_referencia = pd.to_datetime(row['quarter']).strftime('%Y-%m-%d')
            versao = row['version']
            nsd_type = row['nsd_type']

            for (grupo, quadro), params in endpoints_config.items():
                if grupo == "Dados da Empresa":
                    base_url = "https://www.rad.cvm.gov.br/ENET/frmDadosComposicaoCapitalITR.aspx"
                else:
                    base_url = "https://www.rad.cvm.gov.br/ENET/frmDemonstracaoFinanceiraITR.aspx"

                informacao = params["Informacao"]
                demonstracao = params["Demonstracao"]
                periodo = params["Periodo"]

                query = {
                    "Grupo": grupo,
                    "Quadro": quadro,
                    "NomeTipoDocumento": nome_tipo_documento,
                    "Empresa": empresa,
                    "DataReferencia": data_referencia,
                    "Versao": versao,
                    "CodTipoDocumento": cod_tipo_documento,
                    "NumeroSequencialDocumento": nsd,
                    "NumeroSequencialRegistroCvm": cvm_code,
                    "CodigoTipoInstituicao": 1,
                    "Hash": hash_value,
                    **({"Informacao": informacao} if informacao is not None else {}),
                    **({"Demonstracao": demonstracao} if demonstracao is not None else {}),
                    **({"Periodo": periodo} if periodo is not None else {})
                }

                final_url = base_url + "?" + urlencode(query, quote_via=quote_plus)

                urls.append({
                    "cvm_code": cvm_code,
                    "company_name": empresa,
                    "quarter": data_referencia,
                    "version": versao,
                    "nsd": nsd,
                    "nsd_type": nsd_type,
                    "grupo": grupo,
                    "quadro": quadro,
                    "nome_tipo_documento": nome_tipo_documento, 
                    "cod_tipo_documento": cod_tipo_documento,
                    "url": final_url
                })

        except Exception as e:
            self.log_error(e)
            urls = []

        return urls

    def _process_company_quarter_data(self, row, endpoints_config, scraper=None):
        '''
        '''
        div_id = "UltimaTabela"
        tbl_id = "ctl00_cphPopUp_tbDados"
        tit_id = "TituloTabelaSemBorda"

        company_quarter_data = []  # List to store data for the company in the current quarter

        try:
            if scraper is None:
                scraper = self._init_scraper(url=self.homepage_url)

            # row values
            nsd = row['nsd']
            company_name = row['company_name']
            quarter = row.get("quarter").strftime("%Y-%m") if row.get("quarter") else ""
            version = ''.join(filter(str.isdigit, str(row['version'])))
            cvm_code = row['cvm_code']
            nsd_type = row['nsd_type']
            ticker = row['ticker']
            trading_name = row['trading_name']
            ticker_codes = row['ticker_codes']
            isin_codes = row['isin_codes']
            sector = row['sector']
            subsector = row['subsector']
            segment = row['segment']

            # get hash value
            endpoint_nsd = (f"https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={nsd}&CodigoTipoInstituicao=1")

            # Fire off the requests
            r_hash = self._fetch_with_retry(scraper, endpoint_nsd)

            # Parse the response HTML
            html = r_hash.text
            soup = BeautifulSoup(html, "html.parser")
            hash_value = soup.select_one("#hdnHash")["value"]

            # Build the URLs DataFrame
            urls_company_quarter = self.build_urls(row=row, endpoints_config=endpoints_config, hash_value=hash_value)

            quarter_dfs = []
            for i, quarter_item in enumerate(urls_company_quarter):
                grupo = quarter_item['grupo']
                quadro = quarter_item['quadro']
                quarter = quarter_item["quarter"]
                quarter_url = quarter_item['url']
                name = f"{i}_{grupo}_{quadro}"

                r = self._fetch_with_retry(scraper, quarter_url)
                html = r.text
                soup = BeautifulSoup(html, "html.parser")

                temp_folder = self.config.paths["temp_folder"]
                base_name = f"{company_name} {quarter} {version} {nsd} {grupo} {quadro}"

                filename = f"{base_name}.html"
                file_path = os.path.join(temp_folder, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html)

                title_element = soup.find(id=tit_id)
                title = title_element.get_text(strip=True) if title_element else None

                try:
                    if grupo == "Dados da Empresa":

                        table = soup.find("div", id=div_id).find("table") # table inside div
                        df = pd.read_html(StringIO(str(table)))[0]
                        
                        thousand = 1000 if "Mil" in str(df.iloc[0, 0]) else 1

                        acoes_on = self._clean_number(soup.find(id="QtdAordCapiItgz_1").text) * thousand
                        acoes_pn = self._clean_number(soup.find(id="QtdAprfCapiItgz_1").text) * thousand
                        acoes_on_tesouraria = self._clean_number(soup.find(id="QtdAordTeso_1").text) * thousand
                        acoes_pn_tesouraria = self._clean_number(soup.find(id="QtdAprfTeso_1").text) * thousand

                        df = pd.DataFrame([
                            {"account": "00.01.01", "description": "Ações ON Circulação", "value": acoes_on},
                            {"account": "00.01.02", "description": "Ações PN Circulação", "value": acoes_pn},
                            {"account": "00.02.01", "description": "Ações ON Tesouraria", "value": acoes_on_tesouraria},
                            {"account": "00.02.02", "description": "Ações PN Tesouraria", "value": acoes_pn_tesouraria},
                        ])

                    else:
                        thousand = 1000 if "Mil" in title else 1
                        table = soup.find("table", id=tbl_id) # table "alone"
                        split_col = 2
                        total_col = 3

                        df1 = pd.read_html(StringIO(str(table)), header=0)[0].iloc[:, 0:total_col] # first 2 columns
                        df2 = pd.read_html(StringIO(str(table)), header=0, thousands=".")[0].iloc[:, 0:total_col].fillna(0) # last colum, number column

                        columns = ["account", "description", "value"]
                        df1.columns = columns
                        df2.columns = columns
                        df = pd.concat([df1.iloc[:, :split_col], df2.iloc[:, split_col:total_col]], axis=1)

                    if df is not None:
                        # Add necessary metadata columns to the DataFrame
                        df = df.assign(
                            nsd=nsd,
                            company_name=company_name,
                            quarter=quarter,
                            version=version,
                            segment=segment,
                            subsector=subsector,
                            sector=sector,
                            type=grupo,
                            frame=quadro,
                            processed=False, 
                        )

                    # Append the processed DataFrame to the list
                    columns, dtypes, primary_keys = self._get_table_structure(self.tbl_statements_raw, self.db_filepath)

                    quarter_dfs.append(df[columns])

                except Exception as e:
                    pass

        except Exception as e:
            self.log_error(e)

        result = pd.concat(quarter_dfs)

        return result

    def get_targets(self, company_info, existing_nsd):
        """
        """
        try:
            # nsd_df keep only valid types
            nsd_df = existing_nsd[existing_nsd["nsd_type"].isin(self.config.domain["statements_types"])]
            df_nsd_company = pd.merge(nsd_df, company_info, on="company_name", how="inner")
            df_companies = df_nsd_company[['company_name', 'cvm_code', 'ticker', 'trading_name']].drop_duplicates().sort_values(by=['company_name']).reset_index(drop=True)

            targets = []
            start_time = time.monotonic()
            for i, row in df_companies.iterrows():
                if i >= 50:
                    break
                company_name = row['company_name']
                cvm_code = row['cvm_code']
                ticker = row['ticker']
                trading_name = row['trading_name']

                company_query = f"""
                        SELECT *
                        FROM {self.tbl_statements_raw}
                        WHERE company_name = ?
                        ORDER BY quarter, version, type, frame, account
                    """
                financial_statements = self.load_data(query=company_query, params=(company_name,), db_filepath=self.db_filepath)

                # pega só a linha da empresa que interessa
                company_df = company_info[ company_info["company_name"] == company_name ]

                # nsd_df: mantém apenas os tipos válidos e da empresa desejada
                nsd_df = existing_nsd[
                    (existing_nsd["nsd_type"].isin(self.config.domain["statements_types"])) &
                    (existing_nsd["company_name"] == company_name)
                ]
                # merge nsd and company info
                df_nsd_company = pd.merge(nsd_df, company_df, on="company_name", how="inner")
                size = len(df_nsd_company)

                # unused dfs
                nsd_company_outer = pd.merge(nsd_df, company_info, on="company_name", how="outer")
                nsd_company_unmatched_df = nsd_company_outer[~nsd_company_outer['company_name'].isin(df_nsd_company['company_name'])]
                
                try:
                    # remove already processed nsd (existing in financial_statements df)
                    target = df_nsd_company[~df_nsd_company["nsd"].isin(financial_statements["nsd"].unique())]
                    lines = len(target)
                except Exception as e:
                    target = df_nsd_company
                    lines = 0

                # Custom sorting to place empty fields last
                if not target.empty:
                    last_order = "ZZZZZZZZZZ"
                    scrape_order = ["sector", "subsector", "segment", "company_name", "quarter", "version"]

                    target.loc[target["sector"] == "", "sector"] = last_order
                    target.loc[target["subsector"] == "", "subsector"] = last_order
                    target.loc[target["segment"] == "", "segment"] = last_order

                    # Order the list by sector, subsector, segment, company_name, quarter, and version
                    target = target.sort_values(by=scrape_order, ascending=True)

                    # Restore empty fields
                    target.loc[target["sector"] == last_order, "sector"] = ""
                    target.loc[target["subsector"] == last_order, "subsector"] = ""
                    target.loc[target["segment"] == last_order, "segment"] = ""

                    date_columns = ['quarter', 'sent_date', 'date_listing', 'last_date', 'date_quotation']
                    for col in date_columns:
                        try:
                            mask_iso = target[col].astype(str).str.contains('-', na=False) & target[col].astype(str).str.contains('T', na=False)
                            mask_brazil = ~mask_iso & target[col].notna()

                            target.loc[mask_iso, col] = pd.to_datetime(target.loc[mask_iso, col], errors='coerce', dayfirst=False)
                            target.loc[mask_brazil, col] = pd.to_datetime(target.loc[mask_brazil, col], errors='coerce', dayfirst=True)
                        except Exception as e:
                            pass

                    targets.append(target)

                extra_info = [cvm_code, ticker, trading_name, company_name, f'{size} lines, {lines} new']
                self.print_info(i, len(df_companies), start_time, extra_info)

            targets = [t for t in targets if isinstance(t, pd.DataFrame) and not t.empty]
            targets = pd.concat(targets) if targets else pd.DataFrame()
        
        except Exception as e:
            self.log_error(e)
            targets = pd.DataFrame()

        return targets

    def main(self, thread=True):
        """Main method to process data."""
        try:
            # Run data
            company_info = self.load_data(table_name=self.tbl_company, db_filepath=self.db_filepath)
            existing_nsd = self.load_data(table_name=self.tbl_nsd, db_filepath=self.db_filepath)

            targets = self.get_targets(company_info, existing_nsd)

            # download size tracking
            shared_bytes = {"total": 0, "threads": {}}
            shared_lock = Lock()

            batch_processor = StatementsProcessor()
            batch_processor.shared_total_bytes = shared_bytes
            batch_processor.shared_lock = shared_lock

            result = batch_processor.run(
                targets, thread=thread, module_name=self.inspect.getmodule(self.inspect.currentframe()).__name__
            )

            # Total Transferred
            if shared_bytes:
                total_mb = shared_bytes["total"]
                print(f'Total download: {self._format_bytes(total_mb)}')

            # Save processed data
            if not result.empty:
                self.save_to_db(dataframe=result, table_name=self.tbl_statements_raw, db_filepath=self.db_filepath)

        except Exception as e:
            self.log_error(f"Error in main: {e}")

        return True
