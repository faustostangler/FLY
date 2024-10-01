import os
import pandas as pd
import yfinance as yf
import sqlite3
import investpy
import quandl
import wbdata
import time
from datetime import datetime

from stocksymbol import StockSymbol
from bcb import sgs
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.foreignexchange import ForeignExchange
from alpha_vantage.cryptocurrencies import CryptoCurrencies
from fredapi import Fred
from polygon import RESTClient

# Yahoo Finance
# Investing.com (via investpy)
# Alpha Vantage - Stock Data
# Alpha Vantage - Forex Data
# Alpha Vantage - Cryptocurrency Data
# Banco Central do Brasil (BCB)
# Quandl
# Polygon.io
# FRED (Federal Reserve Economic Data)
# World Bank (via wbdata)

from utils import system
from utils import settings

class StockMarketScraper:
    def __init__(self):
        """
        Initialize the FinancialRatios class with the provided financial data.
        """
        try:
            self.db_folder = settings.db_folder
            self.db_name = settings.db_name
        except Exception as e:
            system.log_error(f"Error initializing FinancialRatios: {e}")

    def load_data(self, files):
        """
        Load financial data from the database and process it into DataFrames.
        
        Args:
            files (str): The name part of the database file to load.

        Returns:
            dict: A dictionary where keys are sectors and values are DataFrames containing the NSD data for that sector.
        """
        try:
            db_file = os.path.join(self.db_folder, f"{settings.db_name.split('.')[0]} {files}.db")
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Fetch all table names excluding internal SQLite tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()

            dfs = {}
            total_lines = 0
            start_time = time.time()  # Initialize start time for progress tracking
            print(files)

            # Iterate through each table (sector) and process the data
            for i, table in enumerate(tables):
                try:
                    sector = table[0]
                    df = pd.read_sql_query(f"SELECT * FROM {sector}", conn)

                    # Normalize date columns to datetime format
                    df['quarter'] = pd.to_datetime(df['quarter'], errors='coerce')

                    # Normalize numeric columns
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')

                    # Fill missing 'value' with 0
                    df['value'] = df['value'].fillna(0)

                    # Identify rows where 'account' is missing or NaN and 'value' has been set to 0
                    missing_account = df['account'].isna() | df['account'].str.strip().eq('')
                    df.loc[missing_account, 'account'] = '0'  # Set 'account' to '0' (as text) for these rows

                    # Filter out only the latest versions for each group
                    # df, _ = self.filter_newer_versions(df)
                    dfs[sector] = df  # Store the DataFrame with the sector as the key
                    total_lines += len(df)  # Update the total number of processed lines

                    # Display progress using system.print_info
                    extra_info = [f'Loaded {len(df)} items from {sector} in {files}, total {total_lines}']
                    system.print_info(i, extra_info, start_time, len(tables))  # Removed the total_files argument

                    # print('break')
                    # break

                except Exception as e:
                    system.log_error(f"Error processing table {table}: {e}")

            conn.close()
            return dfs

        except Exception as e:
            system.log_error(f"Error loading existing financial statements: {e}")
            return {}

    def load_company_data(self):

        company_data = {}

        try:
            db_file = os.path.join(self.db_folder, f"{settings.db_name}")
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM {settings.company_table}")

            for row in cursor.fetchall():
                company_name = row[settings.company_columns.index('company_name')]
                company_data[company_name] = dict(zip(settings.company_columns, row))

        except Exception as e:
            system.log_error(e)

        return company_data

    def get_merged_df(self, df_statements, df_companies):
        # merge statements and company info

        columns = ['company_name']
        cols_to_merge = columns + ['cvm_code', 'ticker', 'ticker_codes', 'isin_codes', 'listing']
        # Merge the two DataFrames on the 'company_name' column
        df_statements_companies = pd.merge(df_statements, df_companies[cols_to_merge], on=columns, how='left')

        return df_statements_companies

    def get_median_data(self, df):
        # Remover a informação de fuso horário (timezone) antes de converter para períodos
        df.index = df.index.tz_localize(None)

        # Criar uma coluna de trimestre ('Quarter')
        df['quarter'] = df.index.to_period('Q')

        # Calcular a mediana de 'Adj Close' por trimestre
        median = df.groupby('quarter')['value'].median()
        # mean = df.groupby('quarter')['Adj Close'].mean()

        # Convert last_dates to the actual last date of the quarter
        # Using the 'Q' period information from 'Quarter'
        last_quarter_dates = df['quarter'].map(lambda x: x.end_time)

        # Converter as datas para manter apenas a parte da data (sem tempo)
        last_quarter_dates = last_quarter_dates.dt.date.drop_duplicates()

        # Criar um DataFrame com a última data correta de cada trimestre e a mediana trimestral
        quarterly_summary = pd.DataFrame({
            'quarter': last_quarter_dates.values,  # Drop duplicates to keep one last date per quarter
            'median': median.values, 
        })


        return quarterly_summary

    def get_historical_data(self, df_statements_companies, last_date='1950-01-01'):
        # get historical data from yahoo finance
        list_of_tickers = df_statements_companies[['company_name', 'ticker_codes']].drop_duplicates()

        historical_data = {}
        
        # Iterate over each row and process tickers
        for index, row in list_of_tickers.iterrows():
            company_name = row['company_name']
            tickers = row['ticker_codes']

            # Ensure that tickers are passed as a list by splitting any comma-separated string
            tickers = tickers.split(',') if isinstance(tickers, str) else tickers

            for ticker in tickers:
                if ticker:
                    df = yf.download(ticker + '.SA', start=last_date, group_by='ticker', progress=False)
                    df['value'] = df['Adj Close']
                    df = self.get_median_data(df)
                    print(company_name, ticker)

                historical_data[ticker] = df
            # break
        return historical_data

    def create_new_rows(self, df_statements_companies, historical_data):
        price_indicator = '99'
        new_row_type = 'Cotações Históricas'
        new_row_description = 'Cotação Mediana do Trimestre'

        # create new historical data rows
        list_of_quarters = df_statements_companies[['company_name', 'ticker_codes', 'quarter']].drop_duplicates()

        new_rows = []
        for i, row in list_of_quarters.iterrows():
            company_name = row['company_name']
            quarter = row['quarter']
            tickers = row['ticker_codes']

            tickers = tickers.split(',') if isinstance(tickers, str) else tickers
            for ticker in tickers:
                if ticker:
                    # Separate ticker into no digits and only digits
                    tick = ''.join([char for char in ticker if not char.isdigit()])  # Ticker without digits
                    ticker_digit = ''.join([char for char in ticker if char.isdigit()])  # Only digits

                    mask = df_statements_companies['company_name'] == company_name
                    mask&= df_statements_companies['quarter'] == quarter
                    mask&= df_statements_companies['ticker'] == tick

                    new_row = df_statements_companies[mask].iloc[0].copy()

                    # Modify the necessary columns in the copied row
                    new_row['type'] = new_row_type
                    new_row['frame'] = settings.tipos_acoes[ticker_digit]
                    new_row['account'] = f'{price_indicator}.{ticker_digit}'  # ticker_digit is assumed to be extracted from the original ticker
                    new_row['description'] = new_row_description

                    # Ensure 'quarter' in 'historical_data' is converted to datetime
                    df_historical_data = historical_data.get(tick + ticker_digit, pd.DataFrame())  # Use .get() to avoid KeyError if key doesn't exist
                    if df_historical_data.empty:
                        new_value = pd.NA
                    else:
                        df_historical_data['quarter'] = pd.to_datetime(df_historical_data['quarter'])

                        # Filter the 'historical_data' for the correct 'quarter' and get the 'median' value
                        mask = df_historical_data['quarter'] == pd.to_datetime(quarter)
                        new_value = df_historical_data[mask]['median'].values

                        # If no values are found, set to pd.NA
                        if len(new_value) == 0:
                            new_value = pd.NA
                        else:
                            new_value = new_value[0]  # Extract the actual median value

                    # Set the new value in the new row
                    new_row['value'] = new_value

                    new_rows.append(new_row)

        return new_rows

    def close_db(self):
        """Fecha a conexão com o banco de dados SQLite."""
        if self.conn:
            self.conn.close()
            print("SQLite connection closed.")

    def main(self):
        try:
            # company statements
            statements_data = self.load_data(settings.statements_standard)
            
            # company info
            all_companies = self.load_company_data()
            df_companies = pd.DataFrame(all_companies).T.reset_index(drop=True)

            dict_of_df_statements = {}

            # process company stataments_data per sector
            for i, (sector, df_statements) in enumerate(statements_data.items()):
                print(i, sector, len(df_statements))
                df_statements_companies = self.get_merged_df(df_statements, df_companies)

                historical_data = self.get_historical_data(df_statements_companies)

                new_rows = self.create_new_rows(df_statements_companies, historical_data)
            
                # insert new rows into df_statements_companies

                df_final = pd.concat([df_statements_companies, pd.DataFrame(new_rows)], ignore_index=True).drop_duplicates()

                # sort, clean
                # code here
                dict_of_df_statements[sector] = df_final

        # save to db
        # code here

        except Exception as e:
            system.log_error(e)

        return dict_of_df_statements

