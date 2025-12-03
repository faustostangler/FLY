import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
from threading import Lock
import os

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from utils.base_processor import BaseProcessor

class StockProcessor(BaseProcessor):
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

        # columns
        self.historical_stock_data_all_columns = self.config.domain['historical_stock_data_all_columns']
        self.historical_stock_data_columns = self.config.domain['historical_stock_data_columns']
    def process_instance(self, sub_batch, payload, progress):
        """Process a single batch by delegating to process_batch."""
        result = pd.DataFrame()  # Return an empty DataFrame on failure

        try:
            print(
                f"Starting batch {progress['batch_index']+1}/{progress['total_batches']} "
                f"{100 * (progress['batch_index']+1) / progress['total_batches']:.02f}%"
            )
            batch_processor = StockProcessor()

            # Inject shared control
            batch_processor.shared_total_bytes = self.shared_total_bytes
            batch_processor.shared_lock = self.shared_lock
            batch_processor.thread_id = progress["thread_id"]  # <- inject thread_id

            # Delegate to process_batch for the actual batch processing
            result, benchmark_results = batch_processor.benchmark_function(
                batch_processor.process_batch, sub_batch, payload, progress, benchmark_mode=False
            )

            # Show subtotal download size
            if self.shared_total_bytes and self.shared_lock and progress.get("thread_id") is not None:
                with self.shared_lock:
                    subtotal = self.shared_total_bytes["threads"].get(progress["thread_id"], 0)
                    print(f"Worker {progress['thread_id']} download: {self._format_bytes(subtotal)}")

            # # Save result to database
            # self.save_to_db(dataframe=result, table_name=self.tbl_stock_data, db_filepath=self.db_filepath, alert=False)

        except Exception as e:
            self.log_error(f"Error in process_instance: {e}")

        return result

    def process_instance_old(self, sub_batch, payload, progress):
        """Process a single batch by delegating to process_batch."""
        try:
            return self.process_batch(sub_batch, progress)
        except Exception as e:
            self.log_error(f"Error in process_instance: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on failure

    def process_batch_old(self, sub_batch, progress):
        """"""
        try:
            table_id = "tblResDiario"

            processed_batch = []
            start_time = time.monotonic()
            for i, (_, row) in enumerate(sub_batch.iterrows()):
                company_ticker = row.iloc[0]
                year = row.iloc[1]
                month = row.iloc[2]

                url = f"https://bvmf.bmfbovespa.com.br/sig/FormConsultaMercVista.asp?strTipoResumo=RES_MERC_VISTA&strSocEmissora={company_ticker}&strDtReferencia={month}-{year}&strIdioma=P&intCodNivel=2&intCodCtrl=160"

                headers = self.header_random()  # Use the random headers from the system module
                self.test_internet()
                response = requests.get(url, headers=headers, verify=False)
                response.raise_for_status()
                html = response.text
                soup = BeautifulSoup(html, "html.parser")

                # Find the main table with id 'tblResDiario'
                main_table = soup.find("table", id=table_id)

                if main_table:
                    # Extract nested tables that include the words 'Nome da Ação'
                    tables = main_table.find_all("table", recursive=True)

                    for table in tables:
                        if "Nome da Ação" in table.get_text():
                            try:
                                # Convert the table to a string
                                table_html = str(table)

                                # Preprocess: Replace ',' with '.' for decimals and '.' with '' for thousands
                                table_html = table_html.replace(".", "").replace(",", ".")

                                # Wrap the modified HTML string in StringIO
                                html_string = StringIO(table_html)

                                # Read the table with pandas
                                df = pd.read_html(html_string, header=0)[0]
                            except ValueError:
                                print(f"Skipping table for {company_ticker} {year}-{month} due to format issues.")
                                continue

                            # Extract the ticker from the first row
                            ticker_row = df.columns[0]
                            if "(" in ticker_row and ")" in ticker_row:
                                ticker = ticker_row.split("(")[-1].strip(")")
                                stock_type = ticker_row.split()[-2]
                            else:
                                print(f"Unexpected ticker format: {ticker_row}")
                                continue

                            # Rename Columns and Drop the first and last rows
                            df.columns = self.historical_stock_data_columns
                            df = df[1:-1].reset_index(drop=True)  # Reset index after dropping rows

                            df["date"] = pd.to_datetime(df["date"].apply(lambda x: f"{year}-{month}-{x.strip()}"))
                            df["company_ticker"] = company_ticker
                            df["ticker"] = ticker

                            df = df[self.historical_stock_data_all_columns]

                            processed_batch.append(df)

                            extra_info = [
                                f"{i + 1}/{len(sub_batch)} in batch",
                                progress["sub_batch_counter"],
                                company_ticker,
                                year,
                                month,
                                ticker,
                                df["close"].iloc[-1],
                            ]

                else:
                    new_row = {
                        "company_ticker": company_ticker,
                        "date": pd.to_datetime(f"{year}-{month}-01", format="%Y-%m-%d"),
                    }
                    df = pd.DataFrame([new_row], columns=self.historical_stock_data_all_columns)
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                    df = df.fillna("")
                    processed_batch.append(df)
                    extra_info = [
                        f"{i + 1}/{len(sub_batch)} in batch",
                        progress["sub_batch_counter"],
                        company_ticker,
                        year,
                        month,
                    ]

                # Print progress information
                index_number = progress["batch_start"] + progress["sub_batch_start"] + i
                self.print_info(index_number, progress["scrape_size"], progress["start_time"], extra_info)

        except Exception as e:
            self.print_info(e)

        processed_batch_df = pd.concat(processed_batch)

        return processed_batch_df

    def process_batch(self, sub_batch, payload, progress):
        """Process a batch of stock data by scraping and extracting relevant
        information.

        Parameters:
            sub_batch (DataFrame): A subset of stock data to process.
            progress (dict): Progress tracking details.

        Returns:
            DataFrame: A DataFrame containing processed stock data.
        """
        processed_batch = []
        dfs = []

        try:
            start_time = time.monotonic()

            # Initialize batch size tracking
            if self.shared_total_bytes and self.shared_lock and self.thread_id is not None:
                batch_start_bytes = self.shared_total_bytes["threads"].get(self.thread_id, 0)
            else:
                batch_start_bytes = self.total_bytes_transferred

            # create first scraper
            scraper = self._init_scraper(url=self.homepage_url)

            for i, (_, row) in enumerate(sub_batch.iterrows()):
                try:
                    company_ticker = row.iloc[0]
                    year = row.iloc[1]
                    month = row.iloc[2]
                    company_ticker = 'PETR'
                    year = 2020
                    month = 12

                    stock_data = self._fetch_stock_data(company_ticker, year, month, scraper)
                    if stock_data:
                        dfs.append(stock_data)

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
                        # Log progress
                        actual_item = progress["batch_start"] + i + 1
                        total_items = progress["scrape_size"] + 0
                        worker_info = f"Worker {progress['thread_id']} {100 * actual_item / total_items:.02f}% ({actual_item+0}/{total_items})"
                        extra_info = [
                            worker_info,
                            company_ticker, 
                            year, 
                            month, 
                            # nsd,
                            # (nsd_data.get("sent_date").strftime("%Y-%m-%d %H:%M:%S") if nsd_data.get("sent_date") else ""),
                            # nsd_data.get("nsd_type", ""),
                            # nsd_data.get("company_name", ""),
                            # (nsd_data.get("quarter").strftime("%Y-%m") if nsd_data.get("quarter") else ""),
                            f"({formatted_size})", 
                        ]
                        self.print_info(i, len(sub_batch), start_time, extra_info, indent_level=0)

                        # # Save result to database
                        # temp_df = pd.DataFrame(dfs, columns=self.config.domain["columns_nsd"])
                        # self.save_to_db(dataframe=temp_df, table_name=self.table_name, db_filepath=self.db_filepath, alert=False)

                except Exception as e:
                    self.log_error(f"Error processing row {i}: {e}")

            # Combine all processed DataFrames into a single DataFrame
            results = (
                pd.concat(processed_batch, ignore_index=True)
                if processed_batch
                else pd.DataFrame(columns=self.historical_stock_data_all_columns)
            )

        except Exception as e:
            self.log_error(e)

        return results

    def _fetch_stock_data(self, company_ticker, year, month, scraper):
        '''
        '''
        stock_data = []

        if scraper is None:
            scraper = self._init_scraper()

        try:
            # Construct the URL
            endpoint = (
                f"https://bvmf.bmfbovespa.com.br/sig/FormConsultaMercVista.asp?"
                f"strTipoResumo=RES_MERC_VISTA&strSocEmissora={company_ticker}&"
                f"strDtReferencia={month}-{year}&strIdioma=P&intCodNivel=2&intCodCtrl=160"
            )
            # endpoint = 'https://bvmf.bmfbovespa.com.br/sig/FormConsultaMercVista.asp?strTipoResumo=RES_MERC_VISTA&strSocEmissora=LREN&strDtReferencia=01-2025&strIdioma=P&intCodNivel=2&intCodCtrl=160'
            # Fire off the three requests, with automatic retry on blocks
            r1 = self._fetch_with_retry(scraper, endpoint)

            # Parse the response HTML
            html = r1.text
            soup = BeautifulSoup(html, "html.parser")

            # Create a file with nsd as the name
            file_path = os.path.join(self.config.paths["temp_folder"], f"stock_data_{company_ticker}_{year}_{month}.html")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(html)

            # Extract stock data from the HTML Soup
            data = self._extract_stock_data(soup, company_ticker, year, month)

            if data is not None:
                stock_data.append(data)

        except Exception as e:
            self.log_error(e)

        return stock_data

    def _extract_stock_data(self, soup, company_ticker, year, month):
        """Extract stock data from the parsed HTML."""
        table_id = "tblResDiario"
        stock_entry_label = "Nome da Ação"
        result = []
        try:
            main_table = soup.find("table", id=table_id)

            if main_table:
                tables = main_table.find_all("table", recursive=True)
                for table in tables:
                    if stock_entry_label in table.get_text():
                        try:
                            # Parse table into a DataFrame
                            table_html = str(table).replace(".", "").replace(",", ".")
                            df = pd.read_html(StringIO(table_html), header=0)[0]

                            # Extract metadata and clean up DataFrame
                            ticker_row = df.columns[0]
                            if "(" in ticker_row and ")" in ticker_row:
                                result = ticker_row.split("(")[-1].strip(")")

                            # df.columns = self.historical_stock_data_all_columns
                            df = df[1:-1].reset_index(drop=True)
                            df["date"] = pd.to_datetime(df["date"].apply(lambda x: f"{year}-{month}-{x.strip()}"))
                            df["company_ticker"] = company_ticker
                            df["ticker"] = company_ticker

                            result = df[self.historical_stock_data_all_columns]





                            result.append(df)
                        except Exception as e:
                            self.log_error(f"Error parsing table for {company_ticker} {year}-{month}: {e}")
            else:
                # Handle missing table scenario
                df = self._create_empty_dataframe(company_ticker, year, month)
                result.append(df)
        except Exception as e:
            self.log_error(f"Error extracting data: {e}")

        return pd.concat(result, ignore_index=True) if result else None

    def _parse_table_to_dataframe(self, table, year, month, company_ticker):
        """Convert HTML table to a DataFrame."""
        result = pd.DataFrame(columns=self.historical_stock_data_all_columns)
        return result

    def _create_empty_dataframe(self, company_ticker, year, month):
        """Create an empty DataFrame for missing data."""
        try:
            new_row = {
                "ticker_code": company_ticker,
                "date": pd.to_datetime(f"{year}-{month}-01", format="%Y-%m-%d"),
            }
            df = pd.DataFrame([new_row], columns=self.historical_stock_data_all_columns)
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.fillna("")
        except Exception as e:
            self.log_error(e)
            df = pd.DataFrame(columns=self.historical_stock_data_all_columns)

        return df

    def process_instance_old(self, sub_batch, progress):
        """Create a new instance of StatementsDataScraper and run the scraper.

        This ensures each batch has its own WebDriver instance.
        """
        try:
            processor = StockProcessor()

            processed_batch = processor.process_batch(sub_batch, progress)

            processor.close_driver()

        except Exception as e:
            self.log_error(e)

        return processed_batch

    def main_thread_old(self, batch, progress):
        """Process the batches of statements data using concurrent workers for
        sub-batches.

        Parameters:
        - progress (dict): Progress details including current batch, size, and total length.
        - batch (DataFrame): The current batch to be processed.
        - batch_number (int): Batch number for logging or debugging.

        Returns:
        DataFrame: Combined results of processed sub-batches.
        """
        try:
            all_results = []  # To collect results from all futures
            sub_batch_counter = 0  # Initialize thread counter

            with ThreadPoolExecutor(max_workers=self.config.scraping["max_workers"]) as worker_pool_executor:
                sub_batch_size = max(1, len(batch) // self.config.scraping["max_workers"])
                futures = []

                for sub_batch_start in range(0, len(batch), sub_batch_size):
                    sub_batch_progress = progress.copy()
                    sub_batch_progress["sub_batch_counter"] = sub_batch_counter
                    sub_batch_progress["sub_batch_start"] = sub_batch_start

                    # Define the sub-batch
                    sub_batch = batch.iloc[sub_batch_start : sub_batch_start + sub_batch_size]

                    sub_batch_counter += 1  # Increment thread counter

                    future = worker_pool_executor.submit(self.process_instance, sub_batch, sub_batch_progress)
                    futures.append(future)
                    time.sleep(1)

                # Collect results as sub-batches complete
                for future in as_completed(futures):
                    result = future.result()  # Will raise exceptions if any occurred during processing
                    if not result.empty:
                        all_results.append(result)

            # Combine all results into a single DataFrame
            if all_results:
                processed_batch = pd.concat(all_results, ignore_index=True)
            else:
                processed_batch = pd.DataFrame(columns=self.historical_stock_data_all_columns)

        except Exception as e:
            self.log_error(f"Error during threaded batch processing: {e}")
            processed_batch = pd.DataFrame(columns=self.historical_stock_data_all_columns)

        return processed_batch

    def main_sequential_old(self, batch, progress):
        """Sequentially process all scrape targets at once.

        Parameters:
        - batch (DataFrame): DataFrame containing targets to scrape.
        """
        progress["sub_batch_counter"] = 0  # not incremental, sequential thread
        progress["sub_batch_start"] = 0
        try:
            # Process all scrape targets at once without batching
            processed_batch = self.process_instance(batch, progress)

        except Exception as e:
            self.log_error(f"Error during sequential processing: {e}")

        return processed_batch

    def get_targets(self, company_info, stock_info, start_year=2000, start_month=1):
        """Generate scrape targets for missing data combinations."""
        try:
            # # Convert 'date' column to datetime and extract year and month
            # stock_info["date"] = pd.to_datetime(stock_info["date"])
            # stock_info["year"] = stock_info["date"].dt.year.astype(str)
            # stock_info["month"] = stock_info["date"].dt.month.astype(str).str.zfill(2)

            # Create a set of existing combinations for faster lookups
            # existing_combinations = set(tuple(row) for row in stock_info[["company_ticker", "year", "month"]].values)
            existing_combinations = set()  # DEBUG: treat all as missing

            # Get the current year and month
            now = datetime.datetime.now()
            end_year, end_month = now.year, now.month

            # Generate the range of years and months
            years = range(start_year, end_year + 1)
            months = range(1, 12 + 1)  # 1 through 12

            # Get unique company tickers
            company_tickers = company_info["ticker"].unique().tolist()

            # Generate combinations directly and filter in one step
            targets_set = {
                (ticker, f"{year}", f"{month:02}")
                for ticker in company_tickers
                for year in years
                for month in months
                if not (year == end_year and month > end_month)
                and (ticker, f"{year}", f"{month:02}") not in existing_combinations
            }

            # Ensure the current year and month are included for each ticker
            current_year_month = (f"{end_year}", f"{end_month:02}")
            for ticker in company_tickers:
                current_combination = (ticker, *current_year_month)
                targets_set.add(current_combination)

            # Convert to DataFrame
            targets = pd.DataFrame(list(targets_set), columns=["company_ticker", "year", "month"])
            targets = targets.sort_values(by=["company_ticker", "year", "month"], ascending=[True, True, True]).reset_index(drop=True)

        except Exception as e:
            self.logerror(e)
            targets = pd.DataFrame(columns=["company_ticker", "year", "month"])

        return targets

    def main_old(self, thread=True):
        """The main method to scrape NSD data, parse it, and save it to the
        database."""
        try:
            # # Initialize the WebDriver
            # self.driver, self.driver_wait = self._initialize_driver()

            company_info = self.load_data(
                table_name=self.config.databases["raw"]["table"]["company_info"],
                db_filepath=self.config.databases["raw"]["filepath"],
            )
            stock_info = self.load_data(
                table_name=self.config.statements_historical, db_filepath=self.config.stock_filepath
            )

            targets = self.get_targets(company_info, stock_info)

            progress = {}
            progress["scrape_size"] = len(targets)
            progress["batch_size"] = self.config.scraping["batch_size"]

            start_time = time.monotonic()
            progress["start_time"] = start_time
            for batch_counter, batch_start in enumerate(range(0, progress["scrape_size"], progress["batch_size"])):
                progress["batch_counter"] = batch_counter
                progress["batch_start"] = batch_start

                # Slice the DataFrame for the current batch
                batch = targets.iloc[batch_start : batch_start + progress["batch_size"]]

                if thread:
                    # Start with threading
                    processed_batch = self.main_thread(batch, progress)
                else:
                    # Start sequentially
                    processed_batch = self.main_sequential(batch, progress)

                if not processed_batch.empty:
                    self.save_to_db(
                        dataframe=processed_batch,
                        table_name=self.config.statements_historical,
                        db_filepath=self.config.stock_filepath,
                    )

                # stock_raw = self.scrape_url(targets)

        except Exception as e:
            self.log_error(e)

        return True

    def main(self, thread=True):
        """Main method to process data."""
        try:
            # # Initialize the WebDriver
            # self.driver, self.driver_wait = self._initialize_driver()

            # Run necessary data
            company_info = self.load_data(
                table_name=self.config.databases["raw"]["table"]["company_info"],
                db_filepath=self.config.databases["raw"]["filepath"],
            )
            # stock_info = self.load_data(
            #     table_name=self.config.statements_historical, db_filepath=self.config.stock_filepath
            # ) # DEBUG for first run
            stock_info = pd.DataFrame()

            # Identify scrape targets
            targets = self.get_targets(company_info, stock_info)

            # download size tracking
            shared_bytes = {"total": 0, "threads": {}}
            shared_lock = Lock()

            batch_processor = StockProcessor()
            batch_processor.shared_total_bytes = shared_bytes
            batch_processor.shared_lock = shared_lock

            # get targets
            thread = False
            result = batch_processor.run(
                targets, thread=thread, module_name=self.inspect.getmodule(self.inspect.currentframe()).__name__
            )

            # Total Transferred
            if shared_bytes:
                total_mb = shared_bytes["total"]
                print(f'Total download: {self._format_bytes(total_mb)}')

            # # Save processed data
            # if not result.empty:
            #     self.save_to_db(dataframe=result, table_name=self.tbl_stock_data, db_filepath=self.db_filepath)

        except Exception as e:
            self.log_error(f"Error in main: {e}")

        return True

