import os
import pandas as pd
import yfinance as yf
import sqlite3
import time
from datetime import datetime
from utils import system
from utils import settings

class StockMarketScraper:
    def __init__(self):
        """
        Initialize the StockMarketScraper class by loading database settings.
        """
        try:
            self.db_folder = settings.db_folder  # Path to the database folder
            self.db_name = settings.db_name  # Name of the database
        except Exception as e:
            system.log_error(f"Error initializing StockMarketScraper: {e}")

    def load_data(self, files):
        """
        Load financial data from the SQLite database for a given file.
        
        Args:
            files (str): The name part of the database file to load.

        Returns:
            dict: A dictionary where keys are sectors and values are DataFrames containing the NSD data.
        """
        try:
            db_file = os.path.join(self.db_folder, f"{settings.db_name.split('.')[0]} {files}.db")
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Fetch all table names, ignoring internal SQLite tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()

            dfs = {}
            total_lines = 0
            start_time = time.time()  # Initialize start time for progress tracking

            print(files)  # Output the current file being processed

            # Iterate over each table and process the data
            for i, table in enumerate(tables):
                try:
                    sector = table[0]  # Get the sector name
                    df = pd.read_sql_query(f"SELECT * FROM {sector}", conn)  # Load the table into a DataFrame

                    # Clean and normalize the data
                    df['quarter'] = pd.to_datetime(df['quarter'], errors='coerce')  # Normalize date columns
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')  # Normalize numeric columns
                    df['value'] = df['value'].fillna(0)  # Fill missing values with 0

                    # Handle missing 'account' values
                    missing_account = df['account'].isna() | df['account'].str.strip().eq('')
                    df.loc[missing_account, 'account'] = '0'  # Set missing 'account' to '0'

                    dfs[sector] = df  # Store the DataFrame for the sector
                    total_lines += len(df)  # Update total processed lines

                    # Display progress
                    extra_info = [f'Loaded {len(df)} items from {sector} in {files}, total {total_lines}']
                    system.print_info(i, extra_info, start_time, len(tables))

                except Exception as e:
                    system.log_error(f"Error processing table {table}: {e}")

            conn.close()  # Close the connection
            return dfs  # Return the dictionary of DataFrames

        except Exception as e:
            system.log_error(f"Error loading data from {files}: {e}")
            return {}

    def load_company_data(self):
        """
        Load company data from the database.

        Returns:
            dict: Dictionary with company data.
        """
        company_data = {}
        try:
            db_file = os.path.join(self.db_folder, settings.db_name)
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Query company table data
            cursor.execute(f"SELECT * FROM {settings.company_table}")

            for row in cursor.fetchall():
                company_name = row[settings.company_columns.index('company_name')]
                company_data[company_name] = dict(zip(settings.company_columns, row))

            conn.close()  # Close connection after querying

        except Exception as e:
            system.log_error(f"Error loading company data: {e}")

        return company_data

    def get_merged_df(self, df_statements, df_companies):
        """
        Merge financial statements with company data.
        
        Args:
            df_statements (DataFrame): Financial statements data.
            df_companies (DataFrame): Company data.

        Returns:
            DataFrame: Merged DataFrame with financial statements and company data.
        """
        try:
            columns = ['company_name']
            cols_to_merge = columns + ['cvm_code', 'ticker', 'ticker_codes', 'isin_codes', 'listing']

            # Merge the two DataFrames on 'company_name'
            df_statements_companies = pd.merge(df_statements, df_companies[cols_to_merge], on=columns, how='left')

            return df_statements_companies

        except Exception as e:
            system.log_error(f"Error merging data: {e}")
            return pd.DataFrame()

    def get_median_data(self, df):
        """
        Calculate the median of the 'value' column by quarter.

        Args:
            df (DataFrame): The input DataFrame with historical data.

        Returns:
            DataFrame: A summary DataFrame with quarterly median values.
        """
        try:
            df.index = df.index.tz_localize(None)  # Remove timezone information
            df['quarter'] = df.index.to_period('Q')  # Create a 'quarter' column from index

            # Calculate median value per quarter
            median = df.groupby('quarter')['value'].median()

            # Extract last date of each quarter
            last_quarter_dates = df['quarter'].map(lambda x: x.end_time)
            last_quarter_dates = last_quarter_dates.dt.date.drop_duplicates()

            # Create a summary DataFrame
            quarterly_summary = pd.DataFrame({
                'quarter': last_quarter_dates.values,
                'median': median.values,
            })

            return quarterly_summary

        except Exception as e:
            system.log_error(f"Error calculating median data: {e}")
            return pd.DataFrame()

    def get_historical_data(self, df_statements_companies, last_date='1950-01-01'):
        """
        Fetch historical data for company tickers from Yahoo Finance.

        Args:
            df_statements_companies (DataFrame): DataFrame containing company and ticker information.
            last_date (str): Starting date for fetching historical data.

        Returns:
            dict: A dictionary containing historical data for each ticker.
        """
        historical_data = {}
        try:
            list_of_tickers = df_statements_companies[['company_name', 'ticker_codes']].drop_duplicates()

            # Loop over tickers and fetch data
            for index, row in list_of_tickers.iterrows():
                company_name = row['company_name']
                tickers = row['ticker_codes'].split(',') if isinstance(row['ticker_codes'], str) else []

                for ticker in tickers:
                    if ticker:
                        # Download historical data from Yahoo Finance
                        df = yf.download(ticker + '.SA', start=last_date, group_by='ticker', progress=False)
                        df['value'] = df['Adj Close']  # Set value to Adjusted Close price
                        df = self.get_median_data(df)  # Process the median data

                        historical_data[ticker] = df  # Store historical data for the ticker

            return historical_data

        except Exception as e:
            system.log_error(f"Error fetching historical data: {e}")
            return {}

    def create_new_rows(self, df_statements_companies, historical_data):
        """
        Create new rows for historical data in the financial statements.

        Args:
            df_statements_companies (DataFrame): DataFrame containing financial statements and company info.
            historical_data (dict): Dictionary containing historical data for each ticker.

        Returns:
            list: List of new rows created for historical data.
        """
        new_rows = []
        try:
            price_indicator = '99'
            new_row_type = 'Cotações Históricas'
            new_row_description = 'Cotação Mediana do Trimestre'

            list_of_quarters = df_statements_companies[['company_name', 'ticker_codes', 'quarter']].drop_duplicates()

            # Iterate over each quarter and create new rows
            for i, row in list_of_quarters.iterrows():
                company_name = row['company_name']
                quarter = row['quarter']
                tickers = row['ticker_codes'].split(',') if isinstance(row['ticker_codes'], str) else []

                for ticker in tickers:
                    if ticker:
                        # Handle ticker and historical data creation
                        new_row = self.create_new_row(df_statements_companies, company_name, quarter, ticker, historical_data)
                        if new_row:
                            new_rows.append(new_row)

        except Exception as e:
            system.log_error(f"Error creating new rows: {e}")

        return new_rows

    def create_new_row(self, df_statements_companies, company_name, quarter, ticker, historical_data):
        """
        Helper function to create a new row for historical data.

        Args:
            df_statements_companies (DataFrame): DataFrame containing financial statements.
            company_name (str): Company name.
            quarter (str): Quarter identifier.
            ticker (str): Ticker symbol.
            historical_data (dict): Historical data dictionary.

        Returns:
            dict: New row with historical data.
        """
        try:
            # Filtering for matching rows
            mask = (df_statements_companies['company_name'] == company_name) & \
                   (df_statements_companies['quarter'] == quarter) & \
                   (df_statements_companies['ticker'] == ticker)

            new_row = df_statements_companies[mask].iloc[0].copy()

            # Add necessary data fields for the new row
            new_row['type'] = 'Cotações Históricas'
            new_row['account'] = '99'
            new_row['description'] = 'Cotação Mediana do Trimestre'

            # Fetch historical data for the ticker and quarter
            df_historical = historical_data.get(ticker, pd.DataFrame())
            new_value = df_historical[df_historical['quarter'] == pd.to_datetime(quarter)]['median'].values
            new_row['value'] = new_value[0] if len(new_value) > 0 else pd.NA

            return new_row

        except Exception as e:
            system.log_error(f"Error creating new row for ticker {ticker}: {e}")
            return None

    def main(self):
        """
        Main function that coordinates the entire scraping and data processing flow.
        """
        try:
            # Load financial statements data
            statements_data = self.load_data(settings.statements_standard)

            # Load company data
            all_companies = self.load_company_data()
            df_companies = pd.DataFrame(all_companies).T.reset_index(drop=True)

            # Process each sector's statements and merge with company data
            dict_of_df_statements = {}
            for sector, df_statements in statements_data.items():
                df_statements_companies = self.get_merged_df(df_statements, df_companies)
                historical_data = self.get_historical_data(df_statements_companies)

                # Create new rows for the historical data and append to the final DataFrame
                new_rows = self.create_new_rows(df_statements_companies, historical_data)
                df_final = pd.concat([df_statements_companies, pd.DataFrame(new_rows)], ignore_index=True).drop_duplicates()

                dict_of_df_statements[sector] = df_final  # Store final processed DataFrame

            return dict_of_df_statements

        except Exception as e:
            system.log_error(f"Error in main function: {e}")
            return {}

