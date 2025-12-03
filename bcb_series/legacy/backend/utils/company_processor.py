import json
import time
from threading import Lock

import pandas as pd
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from utils.base_processor import BaseProcessor


class CompanyDataProcessor(BaseProcessor):
    """Processar dados de empresas."""

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

        self.homepage_url = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/?language=pt-br"

        # Initialize database and table names
        self.table_name = self.config.databases["raw"]["table"]["company_info"]
        self.db_filepath = self.config.databases["raw"]["filepath"]

        # # Initialize driver and other resources
        # self.driver, self.driver_wait = self._initialize_driver()

    def process_instance(self, sub_batch, payload, verbose, progress):
        """Process a single batch by delegating to process_batch."""
        result = pd.DataFrame()

        try:
            print(
                f"Starting batch {progress['batch_index']+1}/{progress['total_batches']} {100 * (progress['batch_index']+1) / progress['total_batches']:.02f}%"
            )

            batch_processor = CompanyDataProcessor()

            # Injetar o controle compartilhado
            batch_processor.shared_total_bytes = self.shared_total_bytes
            batch_processor.shared_lock = self.shared_lock
            batch_processor.thread_id = progress["thread_id"]  # IMPORTANTE

            # Delegate to process_batch for the actual batch processing
            result, benchmark_results = batch_processor.benchmark_function(
                batch_processor.process_batch, sub_batch, payload, verbose, progress, benchmark_mode=False
            )

            # total download
            if self.shared_total_bytes and self.shared_lock and progress.get("thread_id") is not None:
                with self.shared_lock:
                    subtotal = self.shared_total_bytes["threads"].get(progress["thread_id"], 0)
                    print(f"Worker {progress['thread_id']} download: {self._format_bytes(subtotal)}")

            # Save result to database
            if not result.empty and not result.columns.empty:
                self.save_to_db(
                    dataframe=result, table_name=self.table_name, db_filepath=self.db_filepath, alert=False
                )

        except Exception as e:
            self.log_error(f"Error in process_instance: {e}")

        return result

    @BaseProcessor().profile_generator()
    def process_batch(self, sub_batch, payload, verbose, progress):
        """
        Process a batch of company tickers by fetching their detailed information.

        Args:
            sub_batch (pd.DataFrame): Subset of tickers to process.
            payload (any): Additional data passed to the batch (not used here).
            progress (dict): Progress tracking information (batch index, total size, etc).

        Returns:
            pd.DataFrame: A concatenated DataFrame with the detailed company information.
                        If no data is found or an error occurs, returns an empty DataFrame.
        """
        result = pd.DataFrame()

        try:
            # Initialize an empty list to accumulate the results
            all_data = []

            # Run the timer to measure processing time
            start_time = time.monotonic()

            # download control
            if self.shared_total_bytes and self.shared_lock and self.thread_id is not None:
                batch_start_bytes = self.shared_total_bytes["threads"].get(self.thread_id, 0)
            else:
                batch_start_bytes = self.total_bytes_transferred

            # create first scraper
            scraper = self._init_scraper(url=self.homepage_url)

            # Loop through each row in the sub-batch
            for i, (_, row) in enumerate(sub_batch.iterrows()):
                # Extract ticker symbol from the row
                ticker = row['ticker']

                # Fetch detailed company data for the ticker
                df = self._get_company_data(ticker, scraper)

                # Check if the returned DataFrame is not empty
                if not df.empty:
                    # Append the company data to the list
                    all_data.append(df)

                    # Track bytes transferred after this ticker
                    if self.shared_total_bytes and self.shared_lock and self.thread_id is not None:
                        bytes_after = self.shared_total_bytes["threads"].get(self.thread_id, 0)
                    else:
                        bytes_after = self.total_bytes_transferred
                    bytes_this_item = bytes_after - batch_start_bytes
                    formatted_size = self._format_bytes(bytes_this_item)
                    batch_start_bytes = bytes_after  # <- Atualiza aqui!!

                    # Extract CVM code and company name for logging
                    cvm_code = df['cvm_code'][0]
                    company_name = df['company_name'][0]

                    batch = 1 # self.config.selenium['log_loop']
                    if i % batch == 0 or i == len(sub_batch) - 1:  # Always log last item too
                        # Log progress
                        actual_item = progress["batch_start"] + i + 1
                        total_items = progress["scrape_size"] + 0
                        worker_info = f"Worker download {progress['thread_id']} Item {100 * actual_item / total_items:.2f}% ({actual_item}/{total_items})"
                        extra_info = [
                            worker_info,
                            cvm_code,
                            ticker,
                            company_name,
                            f"({formatted_size})",
                        ]
                        self.print_info(i, len(sub_batch), start_time, extra_info, indent_level=0)

            # After processing all rows, concatenate the collected DataFrames
            if all_data:

                # Total Transfered
                bytes_transferred = self.total_bytes_transferred
                formatted_size = self._format_bytes(bytes_transferred)
                print(f'Downloaded: {formatted_size}')

                result = pd.concat(all_data, ignore_index=True)

        except Exception as e:
            # In case of any error, initialize an empty DataFrame and log the error
            result = pd.DataFrame()
            self.log_error(e)

        return result

    def _extract_codes(self, otherCodes):
        '''
        '''
        try:
            codes = otherCodes or []
            tickers = [o["code"] for o in codes if isinstance(o, dict)]
            isins   = [o["isin"] for o in codes if isinstance(o, dict)]
        except Exception as e:
            self.log_error(e)
        return json.dumps(tickers), json.dumps(isins)

    def _split_industry_classification(self, df):
        '''
        '''
        try:
            parts = df["industryClassification"].str.split("/", expand=True)
            df["sector"]    = parts.get(0).str.strip()
            df["subsector"] = parts.get(1, df["sector"]).str.strip()
            df["segment"]   = parts.get(2, df["sector"]).str.strip()
        except Exception as e:
            self.log_error(e)
        return df

    def _get_company_data(self, ticker, scraper=None):
        """
        Fetch company info, details and shareholders from B3 for the given ticker,
        retrying automatically on blocks. Returns a single‐row DataFrame with
        mapped and cleaned columns, or the ticker string on failure.
        """
        if scraper is None:
            scraper = self._init_scraper(url=self.homepage_url)

        try:
            # Prepare payloads, tokens and endpoints
            payload1 = {"language": "pt-br", "pageNumber": 1, "pageSize": 120, "company": ticker}
            token1   = self.base64_payload(payload1)
            endpoint1 = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyDataCall/GetInitialCompanies/"
            endpoint2 = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyDataCall/GetDetail/"
            endpoint3 = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyDataCall/GetListedFinancial/"

            # Fire off the three requests, with automatic retry on blocks
            r1 = self._fetch_with_retry(scraper, endpoint1 + token1)

            # parse r1 first so we can build token2
            results = r1.json().get("results", [])
            row     = next((i for i in results if i.get("issuingCompany") == ticker), None)
            if not row:
                return pd.DataFrame()  # retorna vazio para essa empresa

            company = pd.DataFrame([row])
            cvm_code = row["codeCVM"]

            # now details & financial endpoints share the same token
            payload2 = {"codeCVM": str(cvm_code), "language": "pt-br"}
            token2   = self.base64_payload(payload2)

            # Build the details DataFrame
            r2 = self._fetch_with_retry(scraper, endpoint2 + token2)
            details_json = r2.json()
            company_details = pd.DataFrame([details_json])
            if not company_details.empty:
                company_details["ticker_codes"], company_details["isin_codes"] = zip(
                    *company_details["otherCodes"].apply(self._extract_codes)
                )
                company_details = self._split_industry_classification(company_details)

                # Define the real key
                merge_key = ["issuingCompany"]

                # Merge based only on issuingCompany
                df = pd.merge(
                    company,
                    company_details,
                    on=merge_key,
                    how="outer",
                    suffixes=("", "_details")
                )

                # Find overlapping columns
                overwrite_columns = [col for col in company_details.columns if col in company.columns and col not in merge_key]

                # Overwrite old columns with _details values
                for col in overwrite_columns:
                    detail_col = f"{col}_details"
                    if detail_col in df.columns:
                        df[col] = df[detail_col].combine_first(df[col])
                        df.drop(columns=[detail_col], inplace=True)
            else:
                df = company

            # Build the shareholders DataFrame
            r3 = self._fetch_with_retry(scraper, endpoint3 + token2)
            sh_data = (r3.json().get("positionShareholders") or {}).get("results", [])
            shareholders = pd.DataFrame(sh_data)
            if not shareholders.empty:
                # drop the summary row and extra columns
                shareholders = shareholders.iloc[:-1, :-1]
                shareholders["cvm_code"] = cvm_code
                shareholders['ticker'] = ticker

                # Attach shareholders JSON
                shareholders['describle'] = shareholders['describle'].map(self.clean_text)

                df["shareholders"] = [
                    shareholders.to_json(orient="records", force_ascii=False)
                ]

            # Map to your final column schema and clean text fields
            mapping = self.config.domain["web_company_columns_mapping"]
            df = self.map_dataframe_columns(df, mapping)

            for col in (
                "ticker",
                "company_name",
                "trading_name",
                "sector",
                "subsector",
                "segment",
                "registrar",
                "main_registrar",
            ):
                if col in df.columns:
                    df[col] = df[col].map(self.clean_text)

            return df

        except Exception as e:
            self.log_error(e)
            return ticker

    def get_web_companies(self):
        """
        Scrape the list of companies listed on B3 from the official site.

        Steps:
        - Initializes a web scraper with session persistence to handle Cloudflare.
        - Accesses the B3 listed companies homepage to set session cookies.
        - Queries paginated API to retrieve all listed companies.
        - Merges all pages into a single DataFrame containing only the 'ticker' column.

        Returns:
            pd.DataFrame: A DataFrame containing the list of company tickers.
        """
        try:
            # Initialize the scraper
            scraper = self._init_scraper(url=self.homepage_url)

            # Container for all companies data
            all_companies = []

            # Run timing the process
            start_time = time.monotonic()

            # First request: page 1
            payload = {"language": "pt-br", "pageNumber": 1, "pageSize": 120}
            token = self.base64_payload(payload)
            endpoint = 'https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyDataCall/GetInitialCompanies/'

            r1 = self._fetch_with_retry(scraper, endpoint + token)
            r1_json = r1.json()

            total_pages = r1_json['page']['totalPages']

            companies = r1_json['results']
            all_companies.extend(companies)

            # Log progress for page 1
            extra_info = [f"page 1, from {companies[0]['issuingCompany']} to {companies[-1]['issuingCompany']}"]
            self.print_info(0, total_pages, start_time, extra_info)

            # Loop through remaining pages: page 2 onwards
            for i in range(2, total_pages + 1):
                success = False
                while not success:
                    try:
                        payload = {"language": "pt-br", "pageNumber": i, "pageSize": 120}
                        token = self.base64_payload(payload)

                        r2 = self._fetch_with_retry(scraper, endpoint + token)
                        r2_json = r2.json()

                        companies = r2_json["results"]
                        all_companies.extend(companies)

                        # Log progress
                        extra_info = [f"page {i}, from {companies[0]['issuingCompany']} to {companies[-1]['issuingCompany']}"]
                        self.print_info(i - 1, total_pages, start_time, extra_info)

                        success = True  # Only mark as success if no exception occurs

                    except Exception as e:
                        # Reset scraper and retry
                        scraper = self._init_scraper(url=self.homepage_url)
                        self.log_error(e)

            # Convert the list of companies into a DataFrame
            df = pd.DataFrame(all_companies)

            # Rename 'issuingCompany' to 'ticker' and keep only the 'ticker' column
            df = df.rename(columns={"issuingCompany": "ticker"})
            df = df[["ticker"]]

        except Exception as e:
            self.log_error(e)
            df = pd.DataFrame()  # Return empty DataFrame if any error occurs

        return df

    def get_targets(self, local_companies, web_companies):
        """
        Garante que web_companies tenha a estrutura de colunas igual à de local_companies,
        e retorna apenas os registros ainda não existentes.
        """
        # Filtra apenas os novos tickers
        try:
            result = web_companies[~web_companies['ticker'].isin(local_companies['ticker'])]
        except Exception as e:
            self.log_error(e)
            result = pd.DataFrame(columns=['ticker'])

        return result

    def main(self, thread=True):
        """Main method to process data."""
        try:
            # download size
            shared_bytes = {"total": 0, "threads": {}}  # inclui total + subtotais por thread
            shared_lock = Lock()

            batch_processor = CompanyDataProcessor()
            batch_processor.shared_total_bytes = shared_bytes
            batch_processor.shared_lock = shared_lock

            # Run existing and new companies
            local_companies = self.load_data(table_name=self.table_name, db_filepath=self.db_filepath)
            web_companies = self.get_web_companies()

            # Identify scrape targets
            targets = self.get_targets(local_companies, web_companies)

            # Exit if no targets
            if targets.empty:
                self.db_optimize(self.config.databases["raw"]["filepath"])
                return True

            # Start batch processing
            result = self.run(
                targets, thread=thread, module_name=self.inspect.getmodule(self.inspect.currentframe()).__name__
            )

            # Total Transfered
            if self.shared_total_bytes:
                total_mb = self.shared_total_bytes["total"]
                print(f'Total download: {self._format_bytes(total_mb)}')

            # Save processed data
            if not result.empty:
                self.save_to_db(result, table_name=self.table_name, db_filepath=self.db_filepath)

        except Exception as e:
            self.log_error(f"Error in main: {e}")

        return True
