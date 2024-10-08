import os
import re
import numpy as np
import pandas as pd
import yfinance as yf
import sqlite3
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from utils import system
from utils import settings

class StockMarketScraper:
    def __init__(self):
        """
        Initialize the StockMarketScraper class by setting up database folder and name.
        
        Attributes:
            db_folder (str): Path to the database folder.
            db_name (str): Name of the database.
        """
        try:
            # Set database folder and name from settings
            self.db_folder = settings.db_folder  # Path to the database folder
            self.db_name = settings.db_name  # Name of the database
            self.print_lock = Lock()

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
            # Construct the database file path based on the provided file name
            db_file = os.path.join(self.db_folder, f"{settings.db_name.split('.')[0]} {files}.db")
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Fetch all table names, ignoring internal SQLite tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()

            # Initialize variables
            dfs = {}
            total_lines = 0
            start_time = time.time()  

            print(files)  # Output the current file being processed

            # Iterate over each table and process the data
            for i, table in enumerate(tables):
                # Get the sector name from the table name
                sector = table[0]  
                already_done = ['CONSUMO_NAO_CICLICO', 'FINANCEIRO']
                already_done = ['COMUNICACOES', 'BENS_INDUSTRIAIS', 'CONSTRUCAO_E_TRANSPORTE', 'CONSUMO_CICLICO', ]
                if sector not in already_done:
                    try:
                        # Load the data from the table into a DataFrame
                        df = pd.read_sql_query(f"SELECT * FROM {sector}", conn)  

                        # Clean and normalize the data
                        # Normalize date columns to datetime
                        df['quarter'] = pd.to_datetime(df['quarter'], errors='coerce')  
                        # Convert the 'value' column to numeric, handling errors
                        df['value'] = pd.to_numeric(df['value'], errors='coerce')  
                        # Fill missing values in 'value' column with 0
                        df['value'] = df['value'].fillna(0)  

                        # Handle missing 'account' values, replacing empty or NaN values with '0'
                        missing_account = df['account'].isna() | df['account'].str.strip().eq('')
                        df.loc[missing_account, 'account'] = '0'  

                        # Store the cleaned DataFrame in the dictionary
                        dfs[sector] = df  
                        total_lines += len(df)  # Update total processed lines

                        # Display progress information
                        extra_info = [f'Loaded {len(df)} items from {sector} in {files}, total {total_lines}']
                        system.print_info(i, len(tables), start_time, extra_info)

                        # print('break')
                        # break

                    except Exception as e:
                        system.log_error(f"Error processing table {table}: {e}")

            conn.close()  # Close the connection
            return dfs  # Return the dictionary of DataFrames

        except Exception as e:
            system.log_error(f"Error loading data from {files}: {e}")
            return {}

    def load_company_data(self):
        """
        Load company data from the SQLite database.

        Returns:
            dict: A dictionary containing company data, where keys are company names and values are column data.
        """
        company_data = {}
        try:
            # Construct the database file path
            db_file = os.path.join(self.db_folder, settings.db_name)
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Query company table data
            cursor.execute(f"SELECT * FROM {settings.company_table}")

            # Iterate over each row to create a dictionary of company data
            for row in cursor.fetchall():
                company_name = row[settings.company_columns.index('company_name')]
                company_data[company_name] = dict(zip(settings.company_columns, row))

            conn.close()  # Close connection after querying

        except Exception as e:
            system.log_error(f"Error loading company data: {e}")

        return company_data

    def save_to_db(self, sector, df):
        """
        Save the transformed data to the SQLite database, creating or replacing tables as necessary.
        Updates existing data and inserts new data.

        Args:
            sector (str): The sector name.
            df (pd.DataFrame): DataFrame containing the transformed data for the sector.
        """
        try:
            # Construct the database path
            db_path = os.path.join(self.db_folder, f"{settings.db_name.split('.')[0]} {settings.markets_file}.db")

            # Use 'with' to manage the database connection context
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                table_name = sector.upper().replace(' ', '_')  # Create a table name from sector name

                # SQL for creating the table if it does not exist
                create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
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
                )
                """
                cursor.execute(create_table_sql)

                # SQL command for INSERT OR REPLACE with ON CONFLICT
                insert_sql = f"""
                INSERT INTO {table_name} 
                (nsd, sector, subsector, segment, company_name, quarter, version, type, frame, account, description, value) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(company_name, quarter, version, type, frame, account, description) DO UPDATE SET
                    nsd=excluded.nsd,
                    sector=excluded.sector,
                    subsector=excluded.subsector,
                    segment=excluded.segment,
                    value=excluded.value
                """

                # Ensure 'quarter' column is datetime and convert it to string format for SQLite compatibility
                df.loc[:, 'quarter'] = pd.to_datetime(df['quarter'], errors='coerce').dt.strftime('%Y-%m-%d')
                
                # Replace NaN and NaT with None for SQLite compatibility
                df = df.where(pd.notnull(df), None)

                # Drop rows where any of the primary key columns are NULL
                pk_columns = ['company_name', 'quarter', 'version', 'type', 'frame', 'account', 'description']
                df = df.dropna(subset=pk_columns)

                # Convert data types explicitly
                df['nsd'] = df['nsd'].astype(int)
                string_columns = ['sector', 'subsector', 'segment', 'company_name', 'quarter', 'version', 'type', 'frame', 'account', 'description']
                for col in string_columns:
                    df[col] = df[col].astype(str)
                df['value'] = pd.to_numeric(df['value'], errors='coerce')

                # Check for non-string 'company_name'
                non_string_company_names = df[~df['company_name'].apply(lambda x: isinstance(x, str))]
                if not non_string_company_names.empty:
                    print("Non-string values found in 'company_name':")
                    print(non_string_company_names)
                    # Handle or remove these rows as appropriate

                # Check for null 'company_name'
                null_company_names = df[df['company_name'].isnull()]
                if not null_company_names.empty:
                    print("Null values found in 'company_name':")
                    print(null_company_names)
                    # Handle or remove these rows as appropriate

                # Convert DataFrame to list of tuples
                data_to_insert = [
                    tuple(None if pd.isnull(value) else value for value in row)
                    for row in df.itertuples(index=False, name=None)
                ]

                # Check for unsupported types in 'data_to_insert'
                for idx, row in enumerate(data_to_insert):
                    for i, value in enumerate(row):
                        if not isinstance(value, (type(None), int, float, str, bytes)):
                            print(f"Row {idx} has unsupported type at parameter {i+1}: {value}, type: {type(value)}")

                # Execute batch insert
                cursor.executemany(insert_sql, data_to_insert)

                # Commit the transaction
                conn.commit()
                print(f'{sector} saved to {db_path}')
            return df
                    
        except Exception as e:
            system.log_error(f"Error saving transformed data to database: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()  # Rollback in case of error to maintain consistency
            raise  # Re-raise the exception to ensure the error is properly handled

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
            # Remove timezone information from index
            df.index = df.index.tz_localize(None)  
            # Create a 'quarter' column from the index
            df['quarter'] = df.index.to_period('Q')  

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

    def get_historical_data(self, df_statements_companies, sector, last_date='1950-01-01'):
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
            start_time = time.time()
            for i, (_, row) in enumerate(list_of_tickers.iterrows()):
                company_name = row['company_name']
                tickers = row['ticker_codes'].split(',') if isinstance(row['ticker_codes'], str) else []

                extra_info = ['STOCK PRICES', sector, company_name, ' '.join(tickers)]
                system.print_info(i, len(list_of_tickers), start_time, extra_info)

                for ticker in tickers:
                    if ticker:
                        # Download historical data from Yahoo Finance
                        df = yf.download(ticker + '.SA', start=last_date, group_by='ticker', progress=False)
                        # Set value to Adjusted Close price
                        df['value'] = df['Adj Close']  
                        # Process the median data
                        if not df.empty:
                            df = self.get_median_data(df)  

                            # Store historical data for the ticker
                            historical_data[ticker] = df  
        except Exception as e:
            system.log_error(f"Error fetching historical data: {e}")
            historical_data = {}

        return historical_data

    def create_new_rows(self, df_statements_companies, historical_data, sector):
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
            list_of_quarters = df_statements_companies[['company_name', 'ticker_codes', 'quarter']].drop_duplicates()

            new_value = 0
            start_time = time.time()
            total_quarters = len(list_of_quarters)  # Store the total number of quarters

            # Iterate over each quarter and create new rows
            for i, (_, row) in enumerate(list_of_quarters.iterrows()):
                company_name = row['company_name']
                quarter = row['quarter']
                tickers = row['ticker_codes'].split(',') if isinstance(row['ticker_codes'], str) else []

                for ticker in tickers:
                    if ticker:
                        # Handle ticker and historical data creation
                        new_row = self.create_new_row(df_statements_companies, company_name, quarter, ticker, historical_data)
                        # If a valid row (pd.Series) is returned, convert it to a dict and add to new_rows list
                        if new_row is not None and isinstance(new_row, pd.Series):
                            new_rows.append(new_row.to_dict())  # Convert Series to dictionary before appending
                            new_value = new_row['value']
                            new_value = 0 if pd.isna(new_value) else round(float(new_value), 2)

                # Print progress when remaining iterations are divisible by an interval
                remaining = total_quarters - i - 1
                if remaining == 0 or remaining % settings.batch_size == 0:  # Print when remaining is divisible by 100 or is the last iteration

                    extra_info = ['ROW', sector, ticker, company_name, quarter.strftime('%Y-%m-%d'), new_value]
                    system.print_info(i, total_quarters, start_time, extra_info)

        except Exception as e:
            system.log_error(f"Error creating new rows: {e}")

        return new_rows

    def create_new_rows_multithread(self, df_statements_companies, historical_data):
        """
        Create new rows for historical data in the financial statements using multithreading.

        Args:
            df_statements_companies (DataFrame): DataFrame containing financial statements and company info.
            historical_data (dict): Dictionary containing historical data for each ticker.

        Returns:
            list: List of new rows created for historical data.
        """
        new_rows = []
        try:
            list_of_quarters = df_statements_companies[['company_name', 'ticker_codes', 'quarter']].drop_duplicates()

            def process_quarter(row, worker_number, item_number):
                try:
                    company_name = row['company_name']
                    quarter = row['quarter']
                    tickers = row['ticker_codes'].split(',') if isinstance(row['ticker_codes'], str) else []

                    for ticker in tickers:
                        if ticker:
                            # Handle ticker and historical data creation
                            new_row = self.create_new_row(df_statements_companies, company_name, quarter, ticker, historical_data)
                            # If a valid row (pd.Series) is returned, convert it to a dict and add to new_rows list
                            if new_row is not None and isinstance(new_row, pd.Series):
                                new_rows.append(new_row.to_dict())  # Convert Series to dictionary before appending
                            # Print progress with worker number and item number
                            new_value = new_row['value']
                            new_value = 0 if pd.isna(new_value) else round(float(new_value), 2)
                            extra_info = [worker_number, company_name, quarter.strftime('%Y-%m-%d'), new_value]
                            with self.print_lock:  # Acquire lock before printing
                                system.print_info(item_number, len(list_of_quarters), time.time(), extra_info)
                except Exception as e:
                    system.log_error(f"Error processing row for company {row['company_name']}, quarter {row['quarter']}: {e}")

            # Use ThreadPoolExecutor to process quarters concurrently
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
                futures = {executor.submit(process_quarter, row, worker_number % settings.max_workers, item_number): item_number for item_number, (worker_number, row) in enumerate(list_of_quarters.iterrows())}

                for future in as_completed(futures):
                    item_number = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        system.log_error(f"Error in future {item_number}: {e}")

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
        new_row = None  # Initialize new_row to None at the start

        try:
            # Split the ticker into 'tick' (non-digits) and 'ticker_type' (digits)
            tick = ''.join(re.findall(r'[^\d]', ticker))  # Extract all non-digit characters
            ticker_type = ''.join(re.findall(r'\d', ticker))  # Extract all digits

            # Set attributes for the new row
            new_row_type = 'Cotações Históricas'
            new_row_frame = 'Cotação Mediana do Trimestre'
            new_row_account = '99.' + ticker_type
            new_row_description = settings.tipos_acoes.get(ticker_type, 'Tipo de Ação Desconhecido')

            # Filtering for matching rows
            mask = (df_statements_companies['company_name'] == company_name) & \
                (df_statements_companies['quarter'] == quarter) & \
                (df_statements_companies['ticker_codes'].str.contains(ticker))

            dff = df_statements_companies[mask]

            # Check if dff has any rows
            if not dff.empty:
                new_row = dff.iloc[0].copy()  # Copy the first row to modify it

                # Add necessary data fields for the new row
                new_row['type'] = new_row_type
                new_row['frame'] = new_row_frame
                new_row['account'] = new_row_account
                new_row['description'] = new_row_description

                # Fetch historical data for the ticker and quarter
                df_historical = historical_data.get(ticker, pd.DataFrame())

                # Check if df_historical is empty
                if not df_historical.empty:
                    # Convert quarter to datetime.date for comparison
                    quarter_date = pd.to_datetime(quarter).date()  # Convert Timestamp to datetime.date

                    # Perform comparison to get the corresponding value
                    new_value = df_historical[df_historical['quarter'] == quarter_date]['median'].values

                    # Assign the 'value' field based on whether new_value has any values
                    if len(new_value) > 0:
                        new_row['value'] = new_value[0]  # Set to the first value if present
                    else:
                        new_row['value'] = pd.NA  # Set to NA if no values are found

                else:
                    new_value = pd.NA  # Assign NA value if no historical data is found

        except Exception as e:
            system.log_error(f"Error creating new row for ticker {ticker}: {e}")

        return new_row

    def main(self):
        """
        Main function that coordinates the entire scraping and data processing flow.

        Returns:
            dict: Dictionary containing final processed data for each sector.
        """
        try:
            # Load financial statements data from the database
            statements_data = self.load_data(settings.statements_standard)

            # Load company data from the database
            all_companies = self.load_company_data()
            df_companies = pd.DataFrame(all_companies).T.reset_index(drop=True)

            # Process each sector's statements and merge with company data
            dict_of_df_statements = {}
            start_time = time.time()
            for i, (sector, df_statements) in enumerate(statements_data.items()):
                # Merge financial statement data with company data
                df_statements_companies = self.get_merged_df(df_statements, df_companies)
                # Fetch historical data for the companies
                historical_data = self.get_historical_data(df_statements_companies, sector)

                # Create new rows for the historical data and append to the final DataFrame
                new_rows = self.create_new_rows(df_statements_companies, historical_data, sector)
                new_rows = pd.DataFrame(new_rows)
                # Concatenate original and new rows, drop duplicates, and sort
                df_final = pd.concat([df_statements_companies, new_rows], ignore_index=True).drop_duplicates(keep='last')
                df_final = df_final.sort_values(by=settings.statements_order, ascending=[True] * len(settings.statements_order))

                # Store the final processed DataFrame for each sector
                df_final = self.save_to_db(sector, df_final[settings.statements_columns])
                dict_of_df_statements[sector] = df_final[settings.statements_columns]

                extra_info = [sector]
                system.print_info(i, len(statements_data))

            return dict_of_df_statements

        except Exception as e:
            system.log_error(f"Error in main function: {e}")
            return {}