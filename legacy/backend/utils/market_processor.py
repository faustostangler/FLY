import datetime
import json
import re
import time
from threading import Lock

import pandas as pd
import yfinance as yf

from utils.base_processor import BaseProcessor


class MarketProcessor(BaseProcessor):
    """Financial Statements."""

    def __init__(self):
        super().__init__()
        self.db_lock = Lock()  # Initialize a threading Lock

        # Initialize the WebDriver
        # self.driver, self.driver_wait = self._initialize_driver()

    def _get_median_data(self, df):
        """Calculate the median of the 'value' column by quarter.

        Args:
            df (DataFrame): The input DataFrame with historical data.

        Returns:
            DataFrame: A summary DataFrame with quarterly median values.
        """
        try:
            # Remove timezone information from index
            df.index = df.index.tz_localize(None)
            # Create a 'quarter' column from the index
            df["quarter"] = df.index.to_period("Q")

            # Calculate median value per quarter
            median = df.groupby("quarter")["value"].median()

            # Extract last date of each quarter
            last_quarter_dates = df["quarter"].map(lambda x: x.end_time)
            last_quarter_dates = last_quarter_dates.dt.date.drop_duplicates()

            # Create a summary DataFrame
            quarterly_summary = pd.DataFrame({"quarter": last_quarter_dates.values, "median": median.values})

            return quarterly_summary

        except Exception as e:
            self.log_error(f"Error calculating median data: {e}")
            return pd.DataFrame()

    def _create_new_rows(self, targets, historical_data, sector):
        """Create new rows for historical data in the financial statements.

        Args:
            targets (DataFrame): DataFrame containing financial statements and company info.
            historical_data (dict): Dictionary containing historical data for each ticker.

        Returns:
            list: List of new rows created for historical data.
        """
        new_rows = []
        try:
            statements_quarters = targets[["company_name", "ticker_codes", "quarter"]].drop_duplicates()

            new_value = 0
            start_time = time.monotonic()
            total_quarters = len(statements_quarters)  # Store the total number of quarters

            # Iterate over each quarter and create new rows
            for i, (_, row) in enumerate(statements_quarters.iterrows()):
                company_name = row["company_name"]
                quarter = row["quarter"]
                tickers = row["ticker_codes"].split(",") if isinstance(row["ticker_codes"], str) else []
                tickers = json.loads(row["ticker_codes"])

                for ticker in tickers:
                    if ticker:
                        # Handle ticker and historical data creation
                        one_row = self._create_one_row(targets, company_name, quarter, ticker, historical_data)
                        # If a valid row (pd.Series) is returned, convert it to a dict and add to new_rows list
                        if one_row is not None and isinstance(one_row, pd.Series):
                            new_rows.append(one_row.to_dict())  # Convert Series to dictionary before appending
                            new_value = one_row["value"]
                            new_value = 0 if pd.isna(new_value) else round(float(new_value), 2)

                # Print progress when remaining iterations are divisible by an interval
                remaining = total_quarters - i - 1
                if (
                    remaining == 0 or remaining % self.config.scraping["batch_size"] == 0
                ):  # Print when remaining is divisible by 100 or is the last iteration
                    extra_info = [
                        "ROW",
                        sector,
                        ticker,
                        company_name,
                        datetime.datetime.strptime(quarter, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m"),
                        new_value,
                    ]
                    self.print_info(i, total_quarters, start_time, extra_info)

        except Exception as e:
            self.log_error(f"Error creating new rows: {e}")

        return new_rows

    def _create_one_row(self, targets, company_name, quarter, ticker, historical_data):
        """Helper function to create a new row for historical data.

        Args:
            targets (DataFrame): DataFrame containing financial statements.
            company_name (str): CompanyData name.
            quarter (str): Quarter identifier.
            ticker (str): Ticker symbol.
            historical_data (dict): Historical data dictionary.

        Returns:
            dict: New row with historical data.
        """
        one_row = None  # Initialize one_row to None at the start

        try:
            # Split the ticker into 'tick' (non-digits) and 'ticker_type' (digits)
            tick = "".join(re.findall(r"[^\d]", ticker))  # Extract all non-digit characters
            tick_type = "".join(re.findall(r"\d", ticker))  # Extract all digits

            # Set attributes for the new row
            one_row_type = "Cotações Históricas"
            one_row_frame = "Cotação Mediana do Trimestre"
            one_row_account = "99." + tick_type
            one_row_description = self.config.domain["tipos_acoes"].get(tick_type, "Tipo de Ação Desconhecido")

            # Filtering for matching rows
            mask = (
                (targets["company_name"] == company_name)
                & (targets["quarter"] == quarter)
                & (targets["ticker_codes"].str.contains(ticker))
            )

            dff = targets[mask]

            # Check if dff has any rows
            if not dff.empty:
                one_row = dff.iloc[0].copy()  # Copy the first row to modify it

                # Add/Update necessary data fields for the new row
                one_row["type"] = one_row_type
                one_row["frame"] = one_row_frame
                one_row["account"] = one_row_account
                one_row["description"] = one_row_description

                # Fetch historical data for the ticker and quarter
                df_historical = historical_data.get(ticker, pd.DataFrame())

                # Check if df_historical is empty
                if not df_historical.empty:
                    # Convert quarter to datetime.date for comparison
                    quarter_date = pd.to_datetime(quarter).date()  # Convert Timestamp to datetime.date

                    # Perform comparison to get the corresponding value
                    new_value = df_historical[df_historical["quarter"] == quarter_date]["median"].values

                    # Assign the 'value' field based on whether new_value has any values
                    if len(new_value) > 0:
                        one_row["value"] = new_value[0]  # Set to the first value if present
                    else:
                        one_row["value"] = pd.NA  # Set to NA if no values are found

                else:
                    new_value = pd.NA  # Assign NA value if no historical data is found

        except Exception as e:
            self.log_error(f"Error creating new row for ticker {ticker}: {e}")

        return one_row

    def main(self, thread=True):
        """The main method to scrape NSD data, parse it, and save it to the
        database."""
        try:
            statements_data = self.load_data(
                table_name=self.config.databases["raw"]["table"]["statements_raw"],
                db_filepath=self.config.databases["raw"]["filepath"],
            )
            companies_data = self.load_data(
                table_name=self.config.databases["raw"]["table"]["company_info"],
                db_filepath=self.config.databases["raw"]["filepath"],
            )

            historical_data = self.load_data(
                table_name=self.config.historical_data, db_filepath=self.config.databases["raw"]["filepath"]
            )

            # Merge the two DataFrames on 'company_name'
            targets = pd.merge(statements_data, companies_data, on=self.config.historical_columns_both, how="left")
            scrape_tickets = targets[
                self.config.historical_columns_both + self.config.historical_columns_new
            ].drop_duplicates()

            historical_data = {}
            last_date = "1950-01-01"
            start_time = time.monotonic()
            for i, (_, row) in enumerate(scrape_tickets.iterrows()):
                company_name = row["company_name"]
                sector = row["sector"]
                # tickers = .split(',') if isinstance(row['ticker_codes'], str) else []
                tickers = json.loads(row["ticker_codes"])
                for ticker in tickers:
                    if ticker:
                        ticker_br = ticker + ".SA"
                        # Download historical data from Yahoo Finance
                        df = yf.download(ticker_br, start=last_date, group_by="ticker", progress=False)

                        try:
                            df.columns = df.columns.droplevel("Ticker")
                        except Exception:
                            pass
                        # Set value to Adjusted Close price
                        try:
                            df["value"] = df["Adj Close"]
                        except Exception:
                            df["value"] = df["Close"]
                        # Process the median data
                        if not df.empty:
                            df = self._get_median_data(df)
                            columns = list(df.columns)
                            df["ticker"] = ticker
                            historical_data[ticker] = df[["ticker"] + columns]

                extra_info = ["STOCK PRICES", sector, company_name, " ".join(tickers)]
                self.print_info(i, len(scrape_tickets), start_time, extra_info)

            historical_data_rows = self._create_new_rows(targets, historical_data, sector)
            new_rows = pd.DataFrame(historical_data_rows)

            result = pd.concat([targets, new_rows], ignore_index=True).drop_duplicates(keep="last")
            result = result.sort_values(
                by=self.config.statements_order, ascending=[True] * len(self.config.statements_order)
            )

            # Save processed data
            if not result.empty:
                self.save_to_db(
                    dataframe=result,
                    table_name=self.config.statements_historical,
                    db_filepath=self.config.databases["raw"]["filepath"],
                )

            pass
        except Exception as e:
            self.log_error(e)

        return True
