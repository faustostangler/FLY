import time
import os
import glob
import sqlite3
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import system
from utils import settings

class MathTransformation:
    """
    A class to perform mathematical transformations on financial data.
    """

    def __init__(self):
        """Initialize the MathTransformation with settings."""
        self.db_folder = settings.db_folder
        self.db_name = settings.db_name

    def get_database_files(self):
            """
            Load existing financial statements from all .db files in the db_folder.

            Returns:
            DataFrame: A DataFrame containing the NSD data from all files.
            """
            included_patterns = [settings.statements_file]
            excluded_patterns = [settings.backup_name, 'math']  # List of patterns to exclude from filenames

            try:
                all_dfs = []

                # Get all .db files in the db_folder that include any of the included_patterns and exclude the excluded_patterns
                database_files = [
                    db_file for db_file in glob.glob(f"{self.db_folder}/*.db")
                    if any(inc in os.path.basename(db_file) for inc in included_patterns)
                    and not any(exc in os.path.basename(db_file) for exc in excluded_patterns)
                ]

                database_files = sorted(database_files,
                    key=os.path.getsize,  # Ordenar pelo tamanho do arquivo
                    reverse=False          # True = Do maior para o menor 6'53
                    )
                
                return database_files

            except Exception as e:
                system.log_error(f"Error loading existing financial statements data: {e}")
                return []

    def filter_newer_versions(self, df):
        """
        Filter and keep only the newest data from groups of (company_name, quarter, type, frame, account).
        
        Args:
            df (pd.DataFrame): DataFrame containing the financial statements data.

        Returns:
            pd.DataFrame: Filtered DataFrame with only the latest versions for each group.
        """
        # Define the columns used for grouping
        group_columns = ['company_name', 'quarter', 'type', 'frame', 'account']
        version_column = 'version'
        
        try:
            # Sort the DataFrame by group_columns and version in descending order
            df_sorted = df.sort_values(by=group_columns + [version_column], ascending=[True, True, True, True, True, False])
            
            # Drop duplicates based on the specified group_columns, keeping only the first (newest) entry
            df_filtered = df_sorted.drop_duplicates(subset=group_columns, keep='first')
            
            return df_filtered
        
        except Exception as e:
            system.log_error(f"Error during filtering newer versions: {e}")
            return pd.DataFrame(columns=settings.statements_columns)

    def split_into_groups(self, df):
        """
        Split the DataFrame into three groups: unmodified, adjust_year_end_balance, and adjust_cumulative_quarter_balances.
        
        Args:
            df (pd.DataFrame): The filtered DataFrame.

        Returns:
            tuple: Three DataFrames for unmodified, adjust_year_end_balance, and adjust_cumulative_quarter_balances groups.
        """
        try:
            # Group 1: Entries that don't need modification
            unmodified_statements = df[~df['account'].str.startswith(tuple(settings.year_end_accounts + settings.cumulative_quarter_accounts))]

            # Group 2: Entries for adjust_year_end_balance
            year_end_balance_statements = df[df['account'].str.startswith(tuple(settings.year_end_accounts))]

            # Group 3: Entries for adjust_cumulative_quarter_balances
            cumulative_quarter_balances_statements = df[df['account'].str.startswith(tuple(settings.cumulative_quarter_accounts))]

            return unmodified_statements, year_end_balance_statements, cumulative_quarter_balances_statements
        
        except Exception as e:
            system.log_error(f"Error during data splitting: {e}")
            return pd.DataFrame(columns=settings.statements_columns), pd.DataFrame(columns=settings.statements_columns), pd.DataFrame(columns=settings.statements_columns)

    def adjust_year_end_balance(self, df):
        """
        Adjust the 'value' column for the last quarter by subtracting the cumulative values of previous quarters.

        Args:
            df (pd.DataFrame): DataFrame containing the financial statements data for the last quarter.

        Returns:
            pd.DataFrame: DataFrame with adjusted values for the last quarter.
        """
        try:
            df = df.copy()  # Ensure we're working on a copy of the DataFrame

            # Pivot the DataFrame to get values for each quarter in columns
            pivot_df = df.pivot_table(index=['company_name', 'type', 'frame', 'account', 'year'],
                                    columns='month', values='value', aggfunc='max').fillna(0).reset_index()

            # Apply the B3 specific adjustments for the last quarter (Q4) using conditional logic
            pivot_df['z12'] = np.where(
                (pivot_df[9] != 0),
                pivot_df[12] - (pivot_df[9] + pivot_df[6] + pivot_df[3]),
                pivot_df[12]
            )

            # Merge the adjusted values back into the original DataFrame
            df = df.merge(
                pivot_df[['company_name', 'type', 'frame', 'account', 'year', 'z12']],
                on=['company_name', 'type', 'frame', 'account', 'year'],
                how='left'
            )

            # Update the original DataFrame with the adjusted 'z12' value where the month is December
            df.loc[df['month'] == 12, 'value'] = df['z12']

            # Drop the temporary 'z06', 'z09', and 'z12' columns
            df.drop(columns=['z12'], inplace=True)

            return df

        except Exception as e:
            system.log_error(f"Error during year-end balance adjustment: {e}")
            return pd.DataFrame(columns=settings.statements_columns)

    def adjust_cumulative_quarter_balances(self, df):
        """
        Adjust the 'value' column for cumulative quarter balances by ensuring each quarter reflects only the change from the previous quarters.

        Args:
            df (pd.DataFrame): DataFrame containing the financial statements data for cumulative quarters.

        Returns:
            pd.DataFrame: DataFrame with adjusted values for all quarters.
        """
        try:
            df = df.copy()  # Ensure we're working on a copy of the DataFrame

            # Pivot the DataFrame to get values for each quarter in columns
            pivot_df = df.pivot_table(index=['company_name', 'type', 'frame', 'account', 'year'],
                                    columns='month', values='value', aggfunc='max').fillna(0).reset_index()

            # Calculate the adjusted values
            pivot_df['z06'] = pivot_df[6] - pivot_df[3]
            pivot_df['z09'] = pivot_df[9] - (pivot_df['z06'] + pivot_df[3])
            pivot_df['z12'] = pivot_df[12] - (pivot_df['z09'] + pivot_df['z06'] + pivot_df[3])

            # Merge the adjusted values back into the original DataFrame
            df = df.merge(pivot_df[['company_name', 'type', 'frame', 'account', 'year', 'z06', 'z09', 'z12']],
                        on=['company_name', 'type', 'frame', 'account', 'year'],
                        how='left')

            # Update the original DataFrame with the adjusted values using vectorized assignment
            df.loc[df['month'] == 6, 'value'] = df['z06']
            df.loc[df['month'] == 9, 'value'] = df['z09']
            df.loc[df['month'] == 12, 'value'] = df['z12']

            # Drop the temporary columns
            df.drop(columns=['z06', 'z09', 'z12'], inplace=True)

            return df

        except Exception as e:
            system.log_error(f"Error during cumulative quarter balance adjustment: {e}")
            return pd.DataFrame(columns=settings.statements_columns)

    def mathmagic(self, db_file):
        with sqlite3.connect(db_file) as conn:
            # Step 1: open database and get statements
            statements = pd.read_sql_query(f"SELECT * FROM {settings.statements_file}", conn)

        # Step 2: Filter to keep only newer versions
        statements = self.filter_newer_versions(statements)

        # Ensure 'quarter' is in datetime format and create 'year' and 'month' columns
        statements['quarter'] = pd.to_datetime(statements['quarter'], errors='coerce')
        statements['year'] = statements['quarter'].dt.year  # Create the 'year' column
        statements['month'] = statements['quarter'].dt.month  # Create the 'month' column

        # Step 3: Split into groups
        unmodified_statements, year_end_balance_statements, cumulative_quarter_balances_statements = self.split_into_groups(statements)
        
        # Step 4: Apply the adjustments
        year_end_balance_statements = self.adjust_year_end_balance(year_end_balance_statements)
        cumulative_quarter_balances_statements = self.adjust_cumulative_quarter_balances(cumulative_quarter_balances_statements)

        # Step 5: Combine all groups back together
        df = pd.concat([unmodified_statements, year_end_balance_statements, cumulative_quarter_balances_statements])
        df.drop(columns=['year', 'month'], inplace=True)

        # Sort values
        df = df.sort_values(by=settings.statements_order)

        # Connect to the SQLite database
        db_file = db_file.replace('statements', 'math')
        conn = sqlite3.connect(db_file)

        # Save the DataFrame to the SQLite database
        with sqlite3.connect(db_file) as conn:
            df.to_sql(f'{settings.statements_file}', conn, if_exists='replace', index=False)

        return len(df)
    
    def main_thread(self):
        """
        Run the math transformations on each database file using multiple threads.
        """
        try:
            # Get the list of database files
            database_files = self.get_database_files()

            total_files = len(database_files)
            start_time = time.time()
            total_lines = 0

            # Use ThreadPoolExecutor to run mathmagic concurrently
            with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
                futures = []
                for i, db_file in enumerate(database_files):
                    futures.append(executor.submit(self.mathmagic, db_file))

                # Track and print the progress
                for i, future in enumerate(as_completed(futures)):
                    extra_info = [db_file.replace('statements', 'math')]
                    system.print_info(i, extra_info, start_time, total_files)
                    future.result()  # This will raise an exception if one occurred in the thread
            return database_files
        
        except Exception as e:
            system.log_error(f"Error during batch processing: {e}")

    def main_sequential(self):
        """
        Run the math transformations on each database file sequentially.
        """
        try:
            # Get the list of database files
            database_files = self.get_database_files()

            total_files = len(database_files)
            start_time = time.time()
            total_lines = 0
            # Process each database file sequentially
            for i, db_file in enumerate(database_files):
                lines = self.mathmagic(db_file)
                total_lines += lines
                # Track and print the progress
                extra_info = [f'{lines} lines', db_file.replace('statements', 'math')]
                system.print_info(i, extra_info, start_time, total_files)
            return database_files

        except Exception as e:
            system.log_error(f"Error during batch processing: {e}")

    def main(self, thread=False):
        # abrir math, abrir statements, comparar e filtrar *** mudar para colocar tudo dentro do db statements, e em tabelas original e math_transformation
        db_file_statements = r'backend/data\b3 statements COMUNICACOES.db'
        db_file_math = db_file_statements.replace(f'{settings.statements_file}', f'{settings.statements_file_math}')

        with sqlite3.connect(db_file_statements) as conn:
            # Step 1: open database and get statements
            statements = pd.read_sql_query(f"SELECT * FROM {settings.statements_file}", conn)
            
        with sqlite3.connect(db_file_statements) as conn:
            # Step 1: open database and get statements
            math_statements = pd.read_sql_query(f"SELECT * FROM {settings.statements_file}", conn)



        if thread != False:
            database_files = self.main_thread()
        else:
            database_files = self.main_sequential()


if __name__ == "__main__":
    transformer = MathTransformation()
    transformer.run_in_batches()
