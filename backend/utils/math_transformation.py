import time
import os
import sqlite3
import pandas as pd
import numpy as np
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

    def load_data(self, files):
        """
        Load financial data from the database.

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
                df, _ = self.filter_newer_versions(df)
                dfs[sector] = df  # Store the DataFrame with the sector as the key
                total_lines += len(df)  # Update the total number of processed lines

                # Display progress using system.print_info
                extra_info = [f'Loaded {len(df)} items from {sector} in {files}, total {total_lines}']
                system.print_info(i, extra_info, start_time, len(tables))  # Removed the total_files argument

            return dfs

        except Exception as e:
            system.log_error(f"Error loading existing financial statements: {e}")
            return {}

    def filter_newer_versions(self, df):
        """
        Filter and keep only the newest data from groups of (company_name, quarter, type, frame, account).

        Args:
            df (pd.DataFrame): DataFrame containing the financial statements data.

        Returns:
            pd.DataFrame: Filtered DataFrame with only the latest versions for each group.
        """
        group_columns = ['company_name', 'quarter', 'type', 'frame', 'account']
        version_column = 'version'

        try:
            df_sorted = df.sort_values(by=group_columns + [version_column], ascending=[True] * len(group_columns) + [False])
            df_filtered = df_sorted.drop_duplicates(subset=group_columns, keep='first')

            # Also return duplicates as an optional output
            df_duplicates = df_sorted[df_sorted.duplicated(subset=group_columns, keep=False) & (df_sorted.duplicated(subset=group_columns + [version_column], keep=False) == False)]

            return df_filtered, df_duplicates

        except Exception as e:
            system.log_error(f"Error during filtering newer versions: {e}")
            return pd.DataFrame(columns=settings.statements_columns), pd.DataFrame(columns=settings.statements_columns)

    def filter_new_entries(self, dict_new, dict_existing):
        """
        Filter out new entries in dict_new that are not present in dict_existing.

        Args:
            dict_new (dict): A dictionary where keys are sectors and values are DataFrames containing the latest data.
            dict_existing (dict): A dictionary where keys are sectors and values are DataFrames containing already processed data.

        Returns:
            dict: A dictionary where keys are sectors and values are DataFrames with entries in dict_new that are not present in dict_existing.
        """
        key_columns = ['company_name', 'quarter', 'type', 'frame', 'account']  # Define columns that will be used as keys for comparison
        new_entries_column = 'version'  # Define the column that will be used to identify the latest version of entries

        filtered_results = {}  # Initialize an empty dictionary to store the filtered results
        start_time = time.time()  # Record the start time to measure processing time for each sector
        total_sectors = len(dict_new)  # Determine the total number of sectors to process
        total_lines = 0  # Initialize a counter to keep track of the total number of new lines identified

        try:
            # Iterate over each sector and its associated DataFrame in the new data dictionary
            for i, (sector, df_new) in enumerate(dict_new.items()):
                if sector in dict_existing:
                    # If the sector exists in both new and existing data, retrieve the existing DataFrame
                    df_existing = dict_existing[sector]

                    # Merge new and existing DataFrames on key columns with an indicator column to show where each row is from
                    df_comparison = pd.merge(df_new, df_existing[key_columns], on=key_columns, how='outer', indicator=True)

                    # Select rows that are only in the new DataFrame (left_only in the merged indicator)
                    df_left_only = df_comparison[df_comparison['_merge'] == 'left_only'].drop(columns=['_merge'])

                    # Select rows that are present in both DataFrames (both in the merged indicator)
                    df_both = df_comparison[df_comparison['_merge'] == 'both'].copy()

                    # Filter out rows where 'account' is NaN or blank after trimming whitespace
                    df_both = df_both[df_both['account'].notna() & df_both['account'].str.strip().astype(bool)]

                    # Sort the DataFrame by key columns and version, descending to have the newest versions at the top
                    df_both = df_both.sort_values(by=key_columns + [new_entries_column], ascending=[True] * len(key_columns) + [False])

                    # Remove entries from df_both that already exist in df_existing based on key columns
                    df_both = df_both[~df_both.set_index(key_columns).index.isin(df_existing.set_index(key_columns).index)]

                    # Concatenate the two DataFrames (df_left_only and filtered df_both) to get the final set of new entries
                    df_filtered = pd.concat([df_left_only, df_both], ignore_index=True)

                    # Determine the number of new entries identified for the current sector
                    size = len(df_filtered)

                    if not df_filtered.empty:
                        # If there are new entries, add them to the filtered results dictionary
                        filtered_results[sector] = df_filtered
                else:
                    # If the sector does not exist in the existing data, add all entries from the new data to the results
                    filtered_results[sector] = df_new
                    size = len(df_new)

                # Update the total count of new lines identified across all sectors
                total_lines += size

                # Prepare information for logging progress
                extra_info = [f'{size} new lines to math from {sector}, total {total_lines}']
                system.print_info(i, extra_info, start_time, total_sectors)

            return filtered_results

        except Exception as e:
            # Log any errors encountered during processing
            system.log_error(f"Error filtering new entries: {e}")
            return {}

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
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def math_create_pivot(self, df):
        """
        Create a pivot table for the 'value' column, transforming the DataFrame to show values for different months in separate columns.

        Args:
            df (pd.DataFrame): The input DataFrame containing financial data.

        Returns:
            pd.DataFrame: A DataFrame with the 'value' column pivoted by month and merged with the original DataFrame.
        """
        try:
            df.to_csv('df.csv')
            # Create a pivot table for the 'value' column
            value_pivot = df.pivot_table(
                index=['company_name', 'type', 'frame', 'account', 'year'],
                columns='month',
                values='value',
                aggfunc='first'
            ).reset_index()

            # Renaming the columns to match the desired format
            value_pivot.columns.name = None

            # Get the available month columns after pivot
            available_months = set(value_pivot.columns) - {'company_name', 'type', 'frame', 'account', 'year'}

            # Define the target months for quarterly data
            target_quarters = [3, 6, 9, 12]

            # Find the closest available month for each target quarter
            closest_months = {}
            for target in target_quarters:
                closest_month = min(available_months, key=lambda x: abs(x - target), default=None)
                if closest_month:
                    closest_months[target] = closest_month

            # Keep only columns for the closest months of each quarter
            columns_to_keep = ['company_name', 'type', 'frame', 'account', 'year'] + list(closest_months.values())
            value_pivot = value_pivot[columns_to_keep]

            # Ensure columns are renamed to standard quarters (3, 6, 9, 12)
            rename_columns = {closest_months[q]: q for q in target_quarters if q in closest_months}
            value_pivot.rename(columns=rename_columns, inplace=True)

            # Merge the pivoted data back with the original dataframe on key columns
            final_df = pd.merge(
                df.drop(columns=['nsd', 'version', 'value', 'quarter', 'month']),  # Drop 'value', 'quarter', 'month' columns to avoid duplication
                value_pivot,
                left_on=['company_name', 'type', 'frame', 'account', 'year'],
                right_on=['company_name', 'type', 'frame', 'account', 'year'],
                how='left'
            )

            # Removing duplicates based on all columns to keep the first occurrence
            final_df = final_df.drop_duplicates(subset=['company_name', 'type', 'frame', 'account', 'year'])

            return final_df

        except Exception as e:
            system.log_error(f"Error during pivot creation: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error


    def math_unpivot(self, df_pivot, df):
        """
        Unpivot the DataFrame to transform month columns back to rows and merge additional columns from the original DataFrame.

        Args:
            df_pivot (pd.DataFrame): The pivoted DataFrame containing financial data by month.
            df (pd.DataFrame): The original DataFrame to merge additional columns from.

        Returns:
            pd.DataFrame: A DataFrame unpivoted back to the original structure with added columns.
        """
        try:
            # Create a new DataFrame by unpivoting the columns 3, 6, 9, and 12
            unpivoted_df = df_pivot.melt(
                id_vars=['company_name', 'type', 'frame', 'account', 'year'],  # Columns to keep
                value_vars=[3, 6, 9, 12],  # Columns to unpivot
                var_name='month',  # Name for the 'variable' column
                value_name='value'  # Name for the 'value' column
            )

            # Create the 'quarter' column based on 'year' and 'month'
            unpivoted_df['quarter'] = pd.to_datetime(unpivoted_df['year'].astype(str) + '-' + unpivoted_df['month'].astype(str) + '-01') + pd.offsets.MonthEnd(0)

            # Sort the filtered DataFrame by company_name and quarter for better readability
            unpivoted_df = unpivoted_df.sort_values(by=['company_name', 'quarter']).reset_index(drop=True)

            # Merge unpivoted DataFrame with the original df on common columns to incorporate additional columns
            merged_df = pd.merge(
                unpivoted_df,
                df[['nsd', 'sector', 'subsector', 'segment', 'company_name', 'quarter', 'version', 'type', 'frame', 'account', 'description']],
                on=['company_name', 'type', 'frame', 'account', 'quarter'],
                how='right'
            )[df.columns]

            return merged_df

        except Exception as e:
            system.log_error(f"Error during unpivot operation: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error

    def adjust_year_end_balance(self, df):
        """
        Adjust the 'value' column for the last quarter by subtracting the cumulative values of previous quarters.

        Args:
            df (pd.DataFrame): DataFrame containing the financial statements data for the last quarter.

        Returns:
            pd.DataFrame: DataFrame with adjusted values for the last quarter.
        """
        try:
            df = df.copy()
            
            # pivot
            df_pivot = self.math_create_pivot(df)

            # mathmagic
            df_pivot[12] = df_pivot[12] - (df_pivot[9] + df_pivot[6] + df_pivot[3])

            # unpivot
            df = self.math_unpivot(df_pivot, df)

            return df

        except Exception as e:
            system.log_error(f"Error during year-end balance adjustment: {e}")
            return pd.DataFrame()

    def adjust_cumulative_quarter_balances(self, df):
        """
        Adjust the 'value' column for cumulative quarter balances by ensuring each quarter reflects only the change from the previous quarters.

        Args:
            df (pd.DataFrame): DataFrame containing the financial statements data for cumulative quarters.

        Returns:
            pd.DataFrame: DataFrame with adjusted values for all quarters.
        """
        try:
            df = df.copy()
            
            # pivot
            df_pivot = self.math_create_pivot(df)

            # mathmagic
            df_pivot[3] = df_pivot[3]
            df_pivot[6] = df_pivot[6] - (df_pivot[3])
            df_pivot[9] = df_pivot[9] - (df_pivot[6] + df_pivot[3])
            df_pivot[12] = df_pivot[12] - (df_pivot[9] + df_pivot[6] + df_pivot[3])

            # unpivot
            df = self.math_unpivot(df_pivot, df)

            return df

        except Exception as e:
            system.log_error(f"Error during cumulative quarter balance adjustment: {e}")
            return pd.DataFrame()

    def mathmagic(self, dict_filtered, batch_index=0):
        """
        Apply mathematical transformations to the filtered data.

        Args:
            dict_filtered (dict): Dictionary containing DataFrames of new data entries to be transformed.

        Returns:
            dict: A dictionary where keys are sectors and values are DataFrames with transformed data.
        """
        try:
            dict_transformed = {}
            total_lines = 0

            print('transform')
            start_time = time.time()  # Record start time for progress tracking
            # Iterate over each sector in the filtered dictionary
            for i, (sector, df) in enumerate(dict_filtered.items()):
                # Ceate 'year' and 'month' columns
                df['quarter'] = pd.to_datetime(df['quarter'])
                df['year'] = df['quarter'].dt.year
                df['month'] = df['quarter'].dt.month

                # Step 1: Split the DataFrame into three groups
                unmodified_statements, year_end_balance_statements, cumulative_quarter_balances_statements = self.split_into_groups(df)

                # Step 2: Apply mathematical transformations
                # 2a: Apply year-end balance adjustments
                if not year_end_balance_statements.empty:
                    year_end_balance_statements = self.adjust_year_end_balance(year_end_balance_statements)

                # 2b: Apply cumulative quarter balance adjustments
                if not cumulative_quarter_balances_statements.empty:
                    cumulative_quarter_balances_statements = self.adjust_cumulative_quarter_balances(cumulative_quarter_balances_statements)

                # Step 3: Combine all transformed groups back together
                transformed_df = pd.concat([unmodified_statements, year_end_balance_statements, cumulative_quarter_balances_statements], ignore_index=True)

                # Drop 'year' and 'month' columns from the transformed DataFrame
                transformed_df = transformed_df.drop(columns=['year', 'month'])

               # Store the transformed data in the dictionary (we will merge with existing data during saving)
                transformed_df.to_csv(f'{sector}_math.csv', index=False)

                dict_transformed[sector] = transformed_df
                size = len(transformed_df)
                total_lines += size

                # Display progress using system.print_info
                extra_info = [f'{size} lines from {sector}, total {total_lines}']
                system.print_info(i, extra_info, start_time, len(dict_filtered))

            return dict_transformed

        except Exception as e:
            system.log_error(f"Error during mathematical transformations: {e}")
            return {}

    def save_to_db(self, data_dict):
        """
        Save the transformed data to the SQLite database, creating or replacing tables as necessary.
        Updates existing data and inserts new data.

        Args:
            data_dict (dict): Dictionary containing DataFrames of transformed data for each sector.
        """
        try:
            # Construct the database path
            db_path = os.path.join(self.db_folder, f"{settings.db_name.split('.')[0]} {settings.statements_file_math}.db")

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                start_time = time.time()
                total_lines = 0
                for i, (sector, df) in enumerate(data_dict.items()):
                    table_name = sector.upper().replace(' ', '_')  # Create a table name from sector name
                    
                    # # SQL for dropping the table if it exists
                    # drop_table_sql = f"DROP TABLE IF EXISTS {table_name}"
                    # cursor.execute(drop_table_sql)
                        
                    # SQL for creating the table
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

                    # SQL command for INSERT OR REPLACE
                    insert_sql = f"""
                    INSERT INTO {table_name} 
                    (nsd, sector, subsector, segment, company_name, quarter, version, type, frame, account, description, value) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(company_name, quarter, version, type, frame, account, description) DO UPDATE SET
                    nsd=excluded.nsd,
                    sector=excluded.sector,
                    subsector=excluded.subsector,
                    segment=excluded.segment,
                    type=excluded.type,
                    frame=excluded.frame,
                    account=excluded.account,
                    description=excluded.description,
                    value=excluded.value
                    """

                    # Prepare the data for bulk insertion
                    df = df.copy()  # Work on a copy to avoid modifying the original DataFrame

                    # Ensure 'quarter' column is datetime and convert it to string format for SQLite compatibility
                    df['quarter'] = pd.to_datetime(df['quarter'], errors='coerce').dt.strftime('%Y-%m-%d')
                   
                    # Replace NaN and NaT with None to make the DataFrame compatible with SQLite
                    df = df.where(pd.notna(df), None)

                    # Convert DataFrame to list of tuples for batch insertion
                    data_to_insert = list(df.itertuples(index=False, name=None))

                    # Execute batch insert
                    cursor.executemany(insert_sql, data_to_insert)

                    conn.commit()  # Commit the transaction to save changes

                    total_lines += len(df)
                    extra_info = [f'{sector}: {len(df)}, {total_lines} lines']
                    system.print_info(i, extra_info, start_time, len(data_dict))

                cursor.close()  # Close the cursor after all operations are complete

        except Exception as e:
            system.log_error(f"Error saving transformed data to database: {e}")

    def process_and_save(self, dict_filtered, batch_index=0):
        """
        Process and save data for a batch of sectors.

        Args:
            batch_data (dict): Dictionary containing data for a batch of sectors.
        """
        # Apply mathematical transformations to the filtered data
        dict_transformed = self.mathmagic(dict_filtered, batch_index)

        # Save the transformed data to the database
        self.save_to_db(dict_transformed)

    def main_thread(self, dict_filtered, dict_math):
        """
        Run the math transformations using multiple threads.

        Args:
            dict_filtered (dict): Dictionary containing filtered data to be processed.
        """
        try:
            total_lines = sum(len(df) for df in dict_filtered.values())
            batch_size = max(1, total_lines // settings.max_workers)

            with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
                futures = []
                for batch_index, start in enumerate(range(0, total_lines, batch_size)):
                    end = min(start + batch_size, total_lines)
                    batch_data = {k: dict_filtered[k] for k in list(dict_filtered.keys())[start:end]}
                    futures.append(executor.submit(lambda data=batch_data: self.process_and_save(data, batch_index)))

                for future in as_completed(futures):
                    future.result()

        except Exception as e:
            system.log_error(f"Error during batch processing: {e}")

    def main_sequential(self, dict_filtered, dict_math):
        """
        Run the math transformations on each sector's data sequentially and save the results.

        Args:
            dict_filtered (dict): Dictionary containing filtered data to be processed.
        """
        try:
            self.process_and_save(dict_filtered, dict_math)
                             
        except Exception as e:
            # Log any errors encountered during the sequential processing
            system.log_error(f"Error during sequential processing: {e}")

    def main(self, thread=False):
        """
        Main function to run the math transformations either sequentially or using multiple threads.

        Args:
            thread (bool): Flag to determine whether to run in thread mode or sequential mode.
        """
        dict_statements = self.load_data(settings.statements_file)
        # dict_math = self.load_data(settings.statements_file_math)
        dict_math = {}
        dict_filtered = self.filter_new_entries(dict_statements, dict_math)

        if thread:
            self.main_thread(dict_filtered, dict_math)
        else:
            self.main_sequential(dict_filtered, dict_math)

if __name__ == "__main__":
    transformer = MathTransformation()
    transformer.main(thread=True)
