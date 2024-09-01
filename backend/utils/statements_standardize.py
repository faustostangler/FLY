import os
import pandas as pd
import sqlite3
import time

from utils import system
from utils import settings
from utils import intel

class StandardizedReport:
    def __init__(self):
        """Initialize the StandardizedReport with settings."""
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
                break
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

    def create_filter_mask(self, df, conditions):
        """
        Create a boolean filter mask based on multiple filter conditions.

        Parameters
        ----------
        df : pandas.DataFrame
            The input dataframe.
        conditions : dict
            A dictionary where each key is a column and the value is another
            dictionary with keys 'condition' and 'value'.

        Returns
        -------
        pandas.Series
            A boolean filter mask for the dataframe.
        """
        try:
            mask = pd.Series(True, index=df.index)
            
            for column, condition_info in conditions.items():
                condition = condition_info.get('condition')
                value = condition_info.get('value')

                if condition == 'exact':
                    mask &= df[column] == value
                elif condition == 'startswith':
                    mask &= df[column].str.startswith(value)
                elif condition == 'endswith':
                    mask &= df[column].str.endswith(value)
                elif condition == 'contains':
                    mask &= df[column].str.contains(value)
                elif condition == 'not_exact':
                    mask &= df[column] != value
                elif condition == 'not_startswith':
                    mask &= ~df[column].str.startswith(value)
                elif condition == 'not_endswith':
                    mask &= ~df[column].str.endswith(value)
                elif condition == 'not_contains':
                    mask &= ~df[column].str.contains(value)
                else:
                    raise ValueError(f"Unknown filter condition: {condition}")

            return mask

        except Exception as e:
            print(f"Error in create_filter_mask: {e}")
            return pd.Series(False, index=df.index)  # Return a mask that excludes all rows if there's an error

    def standardize_report(self, df, report_name, filter_criteria, mask=None):
        """
        Standardize the financial report by filtering the dataframe according to the specified line items.

        Parameters
        ----------
        df : pandas.DataFrame
            The input dataframe containing financial data.
        report_name : str
            The name of the report to be generated.
        filter_criteria : dict
            A dictionary where keys are tuples (new_account, new_description) and values are dictionaries containing
            filter criteria for multiple columns.
        mask : pandas.Series, optional
            Boolean mask to filter the rows to be processed. If None, the entire DataFrame is processed.

        Returns
        -------
        pandas.DataFrame
            The updated dataframe with standardized line items.
        """
        try:
            if mask is not None:
                df_filtered = df[mask].copy()
            else:
                df_filtered = df.copy()

            start_time = time.time()
            sector = df.iloc[0]['sector']
            total = len(filter_criteria)

            # Iterate over each line item description and its criteria for filtering
            for i, ((new_account, new_description), criteria) in enumerate(filter_criteria.items()):
                try:
                    # Create a combined filter mask based on the criteria
                    df_filter_mask = self.create_filter_mask(df_filtered, criteria)

                    # Combine the filter mask with the main mask if provided
                    if mask is not None:
                        df_combined_filter_mask = df_filter_mask & mask
                    else:
                        df_combined_filter_mask = df_filter_mask

                    # Update the DataFrame directly with the standardized line
                    df.loc[df_combined_filter_mask, 'frame'] = report_name
                    df.loc[df_combined_filter_mask, 'account'] = new_account
                    df.loc[df_combined_filter_mask, 'description'] = new_description

                    extra_info = [f'{sector} {report_name} {new_account} - {new_description}']
                    system.print_info(i, extra_info, start_time, total)
                
                except Exception as e:
                    print(f"Error processing line item ({new_account}, {new_description}): {e}")
                    continue  # Continue with the next line item if there's an error

            return df

        except Exception as e:
            print(f"Error in standardize_report: {e}")
            return df  # Return the original DataFrame if there's an error

    def generate_standard_financial_statements(self, df):
        """
        Generates various sections of the financial statements based on the provided DataFrame.

        Parameters:
        df (pd.DataFrame): The input DataFrame containing financial data.

        Returns:
        pd.DataFrame: Combined DataFrame of all generated financial statement sections.
        """
        # Data structure template for financial line item filters:
        # 'Line Item Description': The key represents a string that describes the financial line item.
        # 'filter': Specifies the column name to apply the filter (e.g., 'account' or 'description').
        # 'condition': The filtering condition (e.g., 'exact', 'startswith', 'endswith', 'contains', 'not_exact', 'not_startswith').
        # 'value': The exact value or pattern to be matched in the specified column.
        # 'levelmin' and 'levelmax': (Optional) Specify the minimum and maximum hierarchical levels for structured account filtering.
        template_dict = {
            'New Item Description 1': {'filter': 'column_name', 'condition': 'filter_type', 'value': 'filter_value', 'levelmin': int, 'levelmax': int}, 
            'New Item Description 2': {'filter': 'column_name', 'condition': 'filter_type', 'value': 'filter_value', 'levelmin': int, 'levelmax': int}, 
            # Repeat the structure for additional line items as needed
        }
        sector = df.iloc[0]['sector']

        df.to_csv(f'df_{sector}.csv', index=False)

        standardization_sections = {
            'Composição do Capital': {
                'section_lines': intel.section_0_lines,
                'mask': (df['account'].str.startswith('0')) & (df['description'].notna())
            }, 
            'Balanço Patrimonial Ativo': {
                'section_lines': intel.section_1_lines,
                'mask': (df['account'].str.startswith('1')) & (df['description'].notna())
            }, 
        }

        try:
            start_time = time.time()
            total_sections = len(standardization_sections)

            # Loop through each section in the standardization pack
            for i, (section_name, parameter) in enumerate(standardization_sections.items()):
                extra_info = [sector, section_name]
                system.print_info(i, extra_info, start_time, total_sections)

                # Call the standardize_report method for each section
                df = self.standardize_report(df, section_name, parameter['section_lines'], parameter['mask'])

        except Exception as e:
            system.log_error(f"Error during generate_standard_financial_statements: {e}")
            return pd.DataFrame(columns=settings.statements_columns)

        return df

    def standardize_data(self, dict_df):
        """
        Standardize data for all sectors in the provided dictionary of DataFrames.

        Parameters:
        dict_df (dict): Dictionary where keys are sectors and values are DataFrames.

        Returns:
        dict: Dictionary with standardized DataFrames.
        """

        print('standart data')
        start_time = time.time()
        total = len(dict_df)

        for i, (sector, df) in enumerate(dict_df.items()):
            extra_info = [f'{sector}']
            system.print_info(i, extra_info, start_time, total)

            df = self.generate_standard_financial_statements(df)

        return dict_df

    def main(self):
        dict_df = self.load_data(settings.statements_file_math)

        standardized_dict = self.standardize_data(dict_df)

        return standardized_dict

if __name__ == "__main__":
    standardization = StandardizedReport()
    standardization.main()
