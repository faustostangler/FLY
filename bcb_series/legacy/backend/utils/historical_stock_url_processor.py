import datetime
import time
from io import StringIO
from threading import Lock

import numpy as np
import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup

from utils.base_processor import BaseProcessor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HistoricalStockUrlProcessor(BaseProcessor):
    """Financial Statements."""

    def __init__(self):
        super().__init__()
        self.db_lock = Lock()  # Initialize a threading Lock

        # # Initialize the WebDriver
        # self.driver, self.driver_wait = self._initialize_driver()

    def process_instance(self, sub_batch, payload, progress):
        """Process a single batch by delegating to process_batch."""
        try:
            # print(f'Requesting batch {progress["batch_index"]}/{progress["total_batches"]} {100*progress["batch_index"]/progress["total_batches"]:.02f}%')

            extra_info = [f"Worker {progress['thread_id']}", " ".join(sub_batch)]
            self.print_info(progress["batch_index"], progress["total_batches"], progress["start_time"], extra_info)
            # Delegate to process_batch for the actual batch processing
            result = self.process_batch(sub_batch, progress)

        except Exception:
            pass

        return result

    def process_batch(self, sub_batch, payload, progress):
        """"""
        rows = []
        months = [f"{i:02}" for i in range(1, 13)]  # Generate month strings "01" to "12"

        try:
            start_time = time.monotonic()  # Track the start time for performance logging

            for i, ticker in enumerate(sub_batch):
                urls = self.get_urls(months, ticker)
                rows.extend(urls)

                # extra_info = [ticker, f"{int(len(rows) / len(months)):2} years"]
                # self.print_info(i, len(sub_batch), start_time, extra_info)

        except Exception:
            pass

        ticker_urls = pd.DataFrame(rows).reset_index(drop=True)

        return ticker_urls

    def get_urls(self, months, ticker):
        """"""
        try:
            # Construct the base URL for fetching ticker-specific historical data
            url = f"https://bvmf.bmfbovespa.com.br/sig/FormConsultaHistorico.asp?strTipoResumo=HISTORICO&strSocEmissora={ticker}"

            # Generate randomized headers for the request and check internet connectivity
            headers = self.header_random()
            self.test_internet()

            # Send an HTTP GET request to fetch the page content
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()  # Raise an error if the request fails

            # Parse the HTML response to find the select element containing available years
            soup = BeautifulSoup(response.text, "html.parser")
            select = soup.find("select", {"id": "cboAno"})  # Locate the dropdown for years

            if select:
                # Extract all valid year options from the dropdown
                years = [option.text for option in select.find_all("option") if option.text.isdigit()]
                years.sort()  # Sort years in ascending order

                # Generate all combinations of year and month
                year_month = [(f"{year}", month) for year in years for month in months]

                # Get the current year and month to filter out future dates
                current_year = str(datetime.datetime.now().year).zfill(4)
                current_month = str(datetime.datetime.now().month).zfill(2)
                year_month = [
                    (year, month)
                    for year, month in year_month
                    if (year < current_year) or (year == current_year and month < current_month)
                ]

                # Add rows for each valid year-month combination
                urls = []
                for year, month in year_month:
                    url = {
                        "ticker": ticker,  # Replace with the actual ticker variable if it's dynamic
                        "year": year,
                        "month": month,
                        "url": f"https://bvmf.bmfbovespa.com.br/sig/FormConsultaMercVista.asp?strTipoResumo=RES_MERC_VISTA&strSocEmissora={ticker}&strDtReferencia={month}-{year}&strIdioma=P&intCodNivel=2&intCodCtrl=160",
                    }
                    urls.append(url)

            else:
                # Add a placeholder row if no years are available for the ticker
                urls = [
                    {
                        "ticker": ticker,  # Ticker symbol
                        "year": None,
                        "month": None,
                        "url": None,  # No URL available
                    }
                ]

        except Exception as e:
            self.log_error(e)

        return urls

    def get_targets(self, company_info, ticker_urls):
        """"""
        try:
            # Filter tickers
            tickers_existing = company_info["ticker"].sort_values().unique()
            try:
                tickers_to_remove = ticker_urls["ticker"].unique()
            except Exception:
                tickers_to_remove = []
            targets = np.setdiff1d(tickers_existing, tickers_to_remove)
        except Exception as e:
            self.log_error(e)

        return targets

    def main(self, thread=True):
        """The main method to scrape historical stock data, parse it, and save
        it to the database."""
        try:
            # Run necessary data
            company_info = self.load_data(
                table_name=self.config.databases["raw"]["table"]["company_info"],
                db_filepath=self.config.databases["raw"]["filepath"],
            )
            ticker_urls = self.load_data(
                table_name=self.config.historical_tickers_urls_table,
                db_filepath=self.config.databases["raw"]["filepath"],
            )

            targets = self.get_targets(company_info, ticker_urls)

            # Exit if no targets
            if targets.size == 0:  # Check if the array is empty
                self.db_optimize(self.config.databases["raw"]["filepath"])
                return True

            # Process targets using threading or sequential logic
            processed_batch = self.run(
                targets, thread=thread, module_name=self.inspect.getmodule(self.inspect.currentframe()).__name__
            )

            if not processed_batch.empty:
                self.save_to_db(
                    dataframe=processed_batch,
                    table_name=self.config.historical_tickers_urls_table,
                    db_filepath=self.config.databases["raw"]["filepath"],
                )

        except Exception as e:
            self.log_error(e)

        return True

    def main_original(self, thread=True):
        """The main method to scrape historical stock data, parse it, and save
        it to the database."""
        try:
            # Run necessary data
            company_info = self.load_data(
                table_name=self.config.databases["raw"]["table"]["company_info"],
                db_filepath=self.config.databases["raw"]["filepath"],
            )

            tickers = company_info["ticker"].unique()

            fast_debug_tickers = [
                "UQMU",
                "PTGU",
                "TZRD",
                "QVQP",
                "NNPY",
                "GRDR",
                "BODY",
                "AACL",
                "AYOS",
                "AMCT",
                "ATBC",
                "ABAP",
                "ABPR",
                "ABCC",
                "ABMX",
                "ABGD",
                "SIVR",
                "ABRL",
                "ACEC",
                "FCEF",
                "ACEE",
                "ACHE",
                "ACOV",
                "ACQO",
                "ACPE",
                "QUAT",
                "ADMA",
                "ADDI",
                "ADAG",
                "ADGE",
                "AECY",
                "AEGP",
            ]
            ticker_urls = {}
            months = [f"{i:02}" for i in range(1, 13)]
            dfs = []
            start_time = time.monotonic()
            for i, ticker in enumerate(tickers):
                if ticker in fast_debug_tickers:
                    continue

                ticker_urls[ticker] = []
                urls = []

                url = f"https://bvmf.bmfbovespa.com.br/sig/FormConsultaHistorico.asp?strTipoResumo=HISTORICO&strSocEmissora={ticker}"
                self.driver.get(url)
                xpath = '//*[@id="cboAno"]'
                try:
                    years = self.get_options(xpath)

                    if years:
                        years.sort()
                        year_month = [(f"{year}", month) for year in years for month in months]
                        current_year = str(datetime.datetime.now().year).zfill(4)
                        current_month = str(datetime.datetime.now().month).zfill(2)
                        year_month = [
                            (year, month)
                            for year, month in year_month
                            if (year < current_year) or (year >= current_year and month < current_month)
                        ]

                        start_time = time.monotonic()
                        for j, (year, month) in enumerate(year_month):
                            if 1 == 1:
                                url = f"https://bvmf.bmfbovespa.com.br/sig/FormConsultaMercVista.asp?strTipoResumo=RES_MERC_VISTA&strSocEmissora={ticker}&strDtReferencia={month}-{year}&strIdioma=P&intCodNivel=2&intCodCtrl=160"
                                urls.append([ticker, url])
                                headers = self.header_random()
                                self.test_internet()

                                response = requests.get(url, headers=headers, verify=False)
                                response.raise_for_status()

                                # Parse the response HTML
                                html = response.text
                                soup = BeautifulSoup(html, "html.parser")

                                # Locate the table
                                parent_table = soup.find("table", {"id": "tblResDiario"})

                                if not parent_table:
                                    continue

                                nested_tables = parent_table.find_all("table")
                                for table in nested_tables:
                                    try:
                                        cleaned_table = str(table).replace(".", "").replace(",", ".")
                                        df = pd.read_html(StringIO(cleaned_table))[
                                            0
                                        ]  # Convert the table to a DataFrame
                                        table_id = str(df.iloc[0, 0])
                                        if "Nome da Ação" in table_id:
                                            ticker_info = table_id.split(":")[
                                                -1
                                            ].strip()  # Extracts 'ticker_type (ticker)' part
                                            ticker_type, ticker_code = (
                                                ticker_info.split()
                                            )  # Splits 'ticker_type' and '(ticker)'
                                            ticker_code = ticker_code.strip("()")  # Remove parentheses from ticker

                                            # Drop the first row
                                            df = df.iloc[1:].reset_index(drop=True)

                                            # Use the new first row (original second row) as column names
                                            df.columns = df.iloc[0]
                                            df = df.iloc[1:].reset_index(drop=True)
                                            df.columns = self.config.historical_columns

                                            # Drop the last row if the first cell contains 'Total'
                                            if "Total" in str(df.iloc[-1, 0]):
                                                df = df.iloc[:-1]

                                            # Combine year, month, and day to create a full datetime column
                                            df["date"] = pd.to_datetime(
                                                df["date"].apply(
                                                    lambda x: f"{year.zfill(4)}-{month.zfill(2)}-{x.zfill(2)}"
                                                ),
                                                format="%Y-%m-%d",
                                                errors="coerce",
                                            )

                                            df["ticker"] = ticker_code
                                            df["ticker_type"] = ticker_type
                                            df = df[["ticker", "ticker_type"] + self.config.historical_columns]
                                            dfs.append(df)
                                    except Exception:
                                        continue  # Skip tables that can't be converted to a DataFrame

                            extra_info = [ticker, year, month]
                            self.print_info(j, len(year_month), start_time, extra_info, indent_level=1)
                            if j > 3:
                                print("fast debug j break")
                                break
                except Exception:
                    pass

                extra_info = [ticker, f"{len(ticker_urls[ticker])} items"]
                self.print_info(i, len(tickers), start_time, extra_info)
                if i > 35:
                    print("fast debug i break")
                    break
                # print('debug pause')
                # break
                pass
            df = pd.concat(dfs)
        except Exception as e:
            self.log_error(e)
        return df
