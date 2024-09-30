import time
import os
import pandas as pd
import numpy as np
import sqlite3

from utils import settings
from utils import system
from utils import intel


class FinancialRatios:
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

    def save_to_db(self):
        """
        Save the calculated ratios back to the database.
        """
        for sector, df in self.dict_df.items():
            # Save the DataFrame back to the database, example:
            print(f"Saving ratios for sector: {sector}")
            # Implementar lógica de salvamento no banco de dados

    def adjust_dfs_types(self, df, source_types=['Dados da Empresa'], target_types=['DFs Consolidadas', 'DFs Individuais']):
        """
        Conditionally duplicates rows of specific types for other types, 
        based on the prior existence of these types for the same company and quarter.

        Parameters:
        - df (pd.DataFrame): Original DataFrame containing the financial data.
        - source_types (list of str): List of types of rows that will be duplicated. Default: ['Dados da Empresa'].
        - target_types (list of str): List of types to which the rows will be duplicated.
                                    Default: ['DFs Consolidadas', 'DFs Individuais'].

        Returns:
        - pd.DataFrame: Updated DataFrame with the conditional duplications.
        """
        try:
            # Step 1: Identify existing combinations of company_name and quarter for each target_type
            existing_combinations = {}
            for target in target_types:
                existing_keys = df[df['type'] == target][['company_name', 'quarter']].drop_duplicates()
                existing_combinations[target] = existing_keys

            # Step 2: Initialize a list to store all duplicated DataFrames
            all_duplicated_dfs = []

            # Step 3: Loop through each source_type and perform the duplication logic
            for source_type in source_types:
                # Filter the rows of the source_type
                source_df = df[df['type'] == source_type].copy()

                # For each target_type, check where to duplicate
                for target in target_types:
                    # Get the combinations where the target_type already exists
                    target_keys = existing_combinations[target]

                    # Perform a merge to identify which rows from source_df have an existing combination
                    to_duplicate = source_df.merge(target_keys, on=['company_name', 'quarter'], how='inner', suffixes=('', '_target'))

                    if not to_duplicate.empty:
                        # Duplicate the rows and change the 'type' to the target_type
                        duplicated = to_duplicate.copy()
                        duplicated['type'] = target
                        all_duplicated_dfs.append(duplicated)

            # Step 4: Concatenate all the duplications
            if all_duplicated_dfs:
                duplicated_df = pd.concat(all_duplicated_dfs, ignore_index=True)
            else:
                duplicated_df = pd.DataFrame(columns=df.columns)

            # Step 5: Remove the original rows from source_types
            df_filtered = df[~df['type'].isin(source_types)].copy()

            # Step 6: Add the duplications to the DataFrame
            if not duplicated_df.empty:
                df_updated = pd.concat([df_filtered, duplicated_df], ignore_index=True)
            else:
                df_updated = df_filtered.copy()

            # Step 7: Reset index and sort the DataFrame
            df_updated.reset_index(drop=True, inplace=True)
            df_updated = df_updated.sort_values(
                by=['sector', 'subsector', 'segment', 'company_name', 'quarter', 'version', 'type', 'account', 'description']
            ).reset_index(drop=True)

            return df_updated
        except Exception as e:
            system.log_error(f"Error processing: {e}")
            


    def add_indicators(self, df, frame_name, indicator_list):
        """
        Calculates financial indicators and adds them as new rows in the DataFrame.

        Parameters:
        - df (pd.DataFrame): Original DataFrame containing financial data.
        - frame_name (str): Name to identify the new 'frame' for the indicators.
        - indicator_list (list of dict): List of dictionaries with indicator definitions.

        Returns:
        - pd.DataFrame: Updated DataFrame with the new indicator rows.
        """
        # Step 1: Pivot the DataFrame with accounts as columns and include 'quarter' in the index
        pivot_df = df.pivot_table(
            index=['company_name', 'type', 'quarter'],
            columns='account',
            values='value',
            aggfunc='sum',
            fill_value=0  # Replace missing values with 0
        ).reset_index()

        # print("Pivoted DataFrame created successfully.")

        # Step 2: Calculate the Indicators
        for indicator in indicator_list:
            column_name = indicator['description']
            column_account = indicator['account']
            formula = indicator['formula']

            try:
                # Apply the formula
                pivot_df[column_name] = formula(pivot_df)

                # print(f"Indicator '{column_name}' calculated successfully.")

            except KeyError as e:
                print(f"'{column_account} - {column_name}': {e}")
                pivot_df[column_name] = np.nan  # Assign NaN if any required account is missing
            except Exception as e:
                print(f"Error calculating the indicator '{column_name}': {e}")
                pivot_df[column_name] = np.nan  # Assign NaN in case of other errors

        # Step 3: Create New Rows for the Indicators
        new_rows = []

        for indicator in indicator_list:
            account = indicator['account']
            description = indicator['description']

            if description not in pivot_df.columns:
                print(f"Indicator '{description}' was not calculated and will be ignored.")
                continue

            # Extract the calculated values for the indicator
            indicator_values = pivot_df[['company_name', 'type', 'quarter', description]].copy()
            indicator_values.rename(columns={description: 'value'}, inplace=True)
            indicator_values['account'] = account
            indicator_values['description'] = description

            # Assign 'frame' as the provided frame_name to easily identify the new rows
            indicator_values['frame'] = frame_name

            # Fill in the missing columns with information from the original DataFrame
            # Select unique combinations of 'company_name', 'type', and 'quarter'
            metadata = df[['company_name', 'type', 'quarter', 'nsd', 'sector', 'subsector', 'segment', 'version']].drop_duplicates(
                subset=['company_name', 'type', 'quarter'],
                keep='first'
            )

            # Merge with 'metadata' to fill in 'nsd', 'sector', etc.
            indicator_row = indicator_values.merge(
                metadata,
                on=['company_name', 'type', 'quarter'],
                how='left'
            )

            # Reorder the columns to match the original DataFrame
            indicator_row = indicator_row[['nsd', 'sector', 'subsector', 'segment', 'company_name', 'quarter',
                                        'version', 'type', 'frame', 'account', 'description', 'value']]

            # Add to the list of new rows
            new_rows.append(indicator_row)

        # Combine all new indicator rows
        if new_rows:
            new_rows_df = pd.concat(new_rows, ignore_index=True)
            # print("All indicators added successfully.")
        else:
            new_rows_df = pd.DataFrame(columns=df.columns)
            # print("No indicators were added.")

        # Step 4: Add the New Rows to the Original DataFrame
        updated_df = pd.concat([df, new_rows_df], ignore_index=True)

        # Optional: Final Treatment of Values (e.g., Fill NaN with zero)
        # updated_df['value'] = updated_df['value'].fillna(0)

        return updated_df

    def main(self):
        """
        Run the financial ratios calculation using the main thread.
        """
        try:
            dict_df = self.load_data(settings.statements_standard)

            dfs = {}
            for sector, df in dict_df.items():
                df = self.adjust_dfs_types(df)
                df = self.add_indicators(df, 'Relações Entre Ativos e Passivos', intel.indicators_11)
                df = self.add_indicators(df, 'Patrimônio', intel.indicators_11b)
                df = self.add_indicators(df, 'Dívida', intel.indicators_12)
                df = self.add_indicators(df, 'Resultados Fundamentalistas 1', intel.indicators_13)
                df = self.add_indicators(df, 'Resultados Fundamentalistas 2', intel.indicators_14)
                df = self.add_indicators(df, 'Resultados Fundamentalistas 3', intel.indicators_15)
                df = self.add_indicators(df, 'Resultados Fundamentalistas 4', intel.indicators_16)
                df = self.add_indicators(df, 'Análise do Fluxo de Caixa', intel.indicators_17)
                df = self.add_indicators(df, 'Análise do Valor Agregado', intel.indicators_18)

                df.to_csv(f'{sector}_ratios.csv', index=False)
                dfs[sector] = df
            pass
        except Exception as e:
            system.log_error(f"Error initializing MinancialRatios: {e}")

if __name__ == "__main__":
    financial_ratios = FinancialRatios()
    financial_ratios.main()
