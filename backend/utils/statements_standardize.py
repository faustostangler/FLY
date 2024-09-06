import os
import pandas as pd
import numpy as np
import sqlite3
import time

from utils import system
from utils import settings
from utils import intel

class StandardizedReport:
    def __init__(self):
        """
        Initialize the StandardizedReport class with settings from the utils module.
        
        Attributes:
            db_folder (str): The folder path where the database is stored.
            db_name (str): The name of the database file.
        """
        try:
            self.db_folder = settings.db_folder
            self.db_name = settings.db_name
        except Exception as e:
            system.log_error(f"Error initializing StandardizedReport: {e}")

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
                    df, _ = self.filter_newer_versions(df)
                    dfs[sector] = df  # Store the DataFrame with the sector as the key
                    total_lines += len(df)  # Update the total number of processed lines

                    # Display progress using system.print_info
                    extra_info = [f'Loaded {len(df)} items from {sector} in {files}, total {total_lines}']
                    system.print_info(i, extra_info, start_time, len(tables))  # Removed the total_files argument

                    print('braek')
                    break
                except Exception as e:
                    system.log_error(f"Error processing table {table}: {e}")

            conn.close()
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
            pd.DataFrame: DataFrame containing duplicates that were not kept.
        """
        group_columns = ['company_name', 'quarter', 'type', 'frame', 'account']
        version_column = 'version'

        try:
            # Sort and drop duplicates to keep the latest versions
            df_sorted = df.sort_values(by=group_columns + [version_column], ascending=[True] * len(group_columns) + [False])
            df_filtered = df_sorted.drop_duplicates(subset=group_columns, keep='first')

            # Also return duplicates as an optional output
            df_duplicates = df_sorted[df_sorted.duplicated(subset=group_columns, keep=False) & (df_sorted.duplicated(subset=group_columns + [version_column], keep=False) == False)]

            return df_filtered, df_duplicates

        except Exception as e:
            system.log_error(f"Error during filtering newer versions: {e}")
            return pd.DataFrame(columns=settings.statements_columns), pd.DataFrame(columns=settings.statements_columns)

    def apply_criteria_to_dataframe(self, df, criteria):
        """
        Apply a list of criteria to a DataFrame, modifying it based on specified filters and target modifications.

        Parameters:
            df (pd.DataFrame): The DataFrame to modify.
            criteria (list): A list of dictionaries containing target modifications and filters.

        Returns:
            pd.DataFrame: The modified DataFrame after applying all criteria.
        """
        try:
            start_time = time.time()
            total = len(criteria)
            for i, criterion in enumerate(criteria):
                target = criterion.get('target')
                account = target.get('account')
                description = target.get('description')
                filter_criteria = criterion.get('filter')

                # Initialize mask for the entire DataFrame
                mask = pd.Series([True] * len(df))

                # Apply each filter for the current criterion
                for filter_criterion in filter_criteria:
                    filter_column = filter_criterion.get('column')
                    filter_condition = filter_criterion.get('condition')
                    filter_value = filter_criterion.get('value')

                    # Convert filter values to lists for all conditions except 'equals' and 'not_equals'
                    if filter_condition not in ['equals', 'not_equals', 'level_min', 'level_max']:
                        if not isinstance(filter_value, list):
                            filter_value = [filter_value]

                    # Convert DataFrame column to lowercase for case-insensitive comparison
                    df_column_lower = df[filter_column].str.lower() if df[filter_column].dtype == 'O' else df[filter_column]

                    # Apply filter conditions
                    if filter_condition == 'equals':  # Exact match (case insensitive)
                        mask &= df_column_lower == filter_value.lower()
                    elif filter_condition == 'not_equals':  # Not equal to (case insensitive)
                        mask &= df_column_lower != filter_value.lower()
                    elif filter_condition == 'startswith':  # Starts with (case insensitive)
                        mask &= df_column_lower.str.startswith(tuple(map(str.lower, filter_value)))
                    elif filter_condition == 'not_startswith':  # Does not start with (case insensitive)
                        mask &= ~df_column_lower.str.startswith(tuple(map(str.lower, filter_value)))
                    elif filter_condition == 'endswith':  # Ends with (case insensitive)
                        mask &= df_column_lower.str.endswith(tuple(map(str.lower, filter_value)))
                    elif filter_condition == 'not_endswith':  # Does not end with (case insensitive)
                        mask &= ~df_column_lower.str.endswith(tuple(map(str.lower, filter_value)))
                    elif filter_condition == 'contains':  # Contains (case insensitive)
                        mask &= df_column_lower.str.contains('|'.join(map(re.escape, filter_value)), case=False, na=False)
                    elif filter_condition == 'not_contains':  # Does not contain (case insensitive)
                        mask &= ~df_column_lower.str.contains('|'.join(map(re.escape, filter_value)), case=False, na=False)
                    elif filter_condition == 'contains_any':  # Contains any of these (case insensitive)
                        mask &= df_column_lower.str.contains('|'.join(map(re.escape, filter_value)), case=False, na=False)
                    elif filter_condition == 'contains_none':  # Contains none of these (case insensitive)
                        mask &= ~df_column_lower.str.contains('|'.join(map(re.escape, filter_value)), case=False, na=False)
                    elif filter_condition == 'contains_all':  # Contains all of these (case insensitive)
                        for term in filter_value:
                            mask &= df_column_lower.str.contains(term, case=False, na=False)
                    elif filter_condition == 'not_contains_all':  # Does not contain all of these (case insensitive)
                        for term in filter_value:
                            mask &= ~df_column_lower.str.contains(term, case=False, na=False)
                    elif filter_condition == 'level_min':  # Minimum hierarchical level
                        levels = df[filter_column].str.count(r'\.') + 1
                        mask &= levels >= int(filter_value)  # Ensure filter_value is an integer
                    elif filter_condition == 'level_max':  # Maximum hierarchical level
                        levels = df[filter_column].str.count(r'\.') + 1
                        mask &= levels <= int(filter_value)  # Ensure filter_value is an integer
                    else:
                        raise ValueError(f"Unknown filter condition: {filter_condition}")

                # Apply target modifications to rows matching the mask
                df.loc[mask, list(target.keys())] = list(target.values())

                extra_info = [f'{account} - {description}', sum(mask)]
                system.print_info(i, extra_info, start_time, total)

            return df

        except Exception as e:
            system.log_error(f"Error applying criteria to DataFrame: {e}")
            return df

    def generate_standard_financial_statements(self, df):
        """
        Generates various sections of the financial statements based on the provided DataFrame.

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame containing financial data.

        Returns
        -------
        pd.DataFrame
            Combined DataFrame of all generated financial statement sections.
        """
        try:
            sector = df.iloc[0]['sector']

            standardization_sections = {
                'Composição do Capital': intel.section_0_criteria, 
                'Balanço Patrimonial Ativo': intel.section_1_criteria,
                'Balanço Patrimonial Passivo': intel.section_2_criteria,
                'Demonstração do Resultado': intel.section_3_criteria,
                'Demonstração de Fluxo de Caixa': intel.section_6_criteria,
                'Demonstração de Valor Adiconado': intel.section_7_criteria,
            }

            start_time = time.time()
            total_sections = len(standardization_sections)

            # Loop through each section in the standardization pack
            for i, (section_name, criteria) in enumerate(standardization_sections.items()):
                extra_info = [sector, section_name]
                system.print_info(i, extra_info, start_time, total_sections)

                # Call the apply_criteria_to_dataframe method for each section
                df = self.apply_criteria_to_dataframe(df, criteria)

        except Exception as e:
            system.log_error(f"Error during generate_standard_financial_statements: {e}")
            return pd.DataFrame(columns=settings.statements_columns)

        return df

    def standardize_data(self, dict_df):
        """
        Standardize data for all sectors in the provided dictionary of DataFrames.

        Parameters
        ----------
        dict_df (dict): Dictionary where keys are sectors and values are DataFrames.

        Returns
        -------
        dict: Dictionary with standardized DataFrames.
        """
        try:
            print('Standardizing data')
            start_time = time.time()
            total = len(dict_df)

            for i, (sector, df) in enumerate(dict_df.items()):
                df.to_csv(f'df_{sector}.csv', index=False)

                extra_info = [f'{sector}']
                system.print_info(i, extra_info, start_time, total)

                df = self.generate_standard_financial_statements(df)

        except Exception as e:
            system.log_error(f"Error in standardize_data: {e}")
            return {}

        return dict_df

    def main(self):
        """
        Main function to load, process, and standardize financial statement data.

        Returns
        -------
        dict: Dictionary with standardized DataFrames.
        """
        try:
            dict_df = self.load_data(settings.statements_file_math)
            standardized_data = self.standardize_data(dict_df)

            # save_to_db()

            return standardized_data

        except Exception as e:
            system.log_error(f"Error in main method: {e}")
            return {}

if __name__ == "__main__":
    standardization = StandardizedReport()
    standardization.main()
