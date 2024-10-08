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

                    # Display progress
                    extra_info = [f'Loaded {len(df)} items from {sector} in {files}, total {total_lines}']
                    system.print_info(i, len(tables), start_time, extra_info)

                    # print('break')
                    # break

                except Exception as e:
                    system.log_error(f"Error processing table {table}: {e}")

            conn.close()
            return dfs

        except Exception as e:
            system.log_error(f"Error loading existing financial statements: {e}")
            return {}

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
            db_path = os.path.join(self.db_folder, f"{settings.db_name.split('.')[0]} {settings.indicators_fle}.db")

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

    def adjust_dfs_types(self, df, source_types=['Dados da Empresa', 'Cotações Históricas'], target_types=['DFs Consolidadas', 'DFs Individuais']):
        """
        Conditionally duplicates rows of specific types for other types, 
        based on the prior existence of these types for the same company and quarter.

        Parameters:
        - df (pd.DataFrame): Original DataFrame containing the financial data.
        - source_types (list of str): List of types of rows that will be duplicated. Default: ['Dados da Empresa', 'Cotações Históricas'].
        - target_types (list of str): List of types to which the rows will be duplicated.
                                    Default: ['DFs Consolidadas', 'DFs Individuais'].

        Returns:
        - pd.DataFrame: Updated DataFrame with the conditional duplications.
        """

        # The method follows a clear logic:
        # 1. Check what is already present (to avoid redundancies),
        # Identification of Existing Reports: The method starts by examining the financial records already existing for each company in each quarter. It focuses on identifying whether certain types of reports (such as "consolidated" or "individual") already exist for that company and quarter. This step creates a database of what is already present, avoiding unnecessary actions on reports that have not yet been created.
        # 2. Identify what is missing (to fill gaps), and
        # Gap Verification: After identifying what is available, the method looks for complementary types of information (such as "historical quotations" or "company data"). The goal here is to check whether these complementary data can be used to fill gaps in the reports that already exist. It does this by comparing the available information with the existing reports and identifying any missing data.
        # 3. Insert new data only when appropriate, maintaining the consistency and integrity of the financial reports.
        # Conditional Data Duplication: If the method finds a situation where a report already exists (for example, a consolidated report for a specific company in a specific quarter), it then duplicates the additional data (such as quotations or company data) into that report. Duplication happens only when the report is already present, meaning it conditionally fills the gaps and avoids creating unnecessary information.

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
            


    def add_indicators(self, df, frame_name, indicator_list, sector):
        """
        Calculates financial indicators and adds them as new rows in the DataFrame.

        Parameters:
        - df (pd.DataFrame): Original DataFrame containing financial data.
        - frame_name (str): Name to identify the new 'frame' for the indicators.
        - indicator_list (list of dict): List of dictionaries with indicator definitions.

        Returns:
        - pd.DataFrame: Updated DataFrame with the new indicator rows.
        """
        # O método é utilizado para calcular indicadores financeiros específicos, fornecidos por meio de uma lista de definições, e adicionar esses indicadores como novas linhas ao DataFrame original. Isso permite complementar os dados financeiros existentes com cálculos derivados, facilitando a análise financeira.
        # 1. Criação de uma Tabela Dinâmica (Pivot): Primeiro, o DataFrame original é transformado em uma tabela dinâmica, onde as contas financeiras (colunas com diferentes tipos de valores) são organizadas como colunas, e as empresas, tipos de relatório e trimestres formam o índice. O valor correspondente a cada conta é preenchido nas células, substituindo valores ausentes por 0.
        # 2. Cálculo dos Indicadores: Para cada indicador na lista, o método aplica uma fórmula matemática ou lógica aos dados da tabela dinâmica. O resultado é armazenado em uma nova coluna correspondente ao indicador. Se ocorrer algum erro ou se a conta necessária não existir, o valor será preenchido com NaN (não disponível).
        # 3. Criação de Novas Linhas para os Indicadores: Após o cálculo, os valores dos indicadores são reorganizados para se parecerem com as outras linhas do DataFrame original. São criadas novas linhas para cada indicador, associando o valor calculado ao respectivo nome da empresa, trimestre, conta, e descrição do indicador. Além disso, são preenchidas colunas com informações adicionais, como o setor, segmento, e versão, a partir do DataFrame original.
        # 4. Combinação com o DataFrame Original: Por fim, as novas linhas com os indicadores são combinadas com o DataFrame original, criando um DataFrame expandido que contém tanto os dados originais quanto os novos cálculos dos indicadores. Isso resulta em um conjunto de dados completo e atualizado.

        # Step 1: Pivot the DataFrame with accounts as columns and include 'quarter' in the index
        pivot_df = df.pivot_table(
            index=['company_name', 'type', 'quarter'],
            columns='account',
            values='value',
            aggfunc='sum',
            fill_value=0  # Replace missing values with 0
        ).reset_index()
        
        df2 = df.copy()
        df2['account_description'] = df2['account'] + ' - ' + df2['description']
        # Now pivot the DataFrame using the new 'account_description' column
        pivot_df2 = df2.pivot_table(
            index=['company_name', 'type', 'quarter'],
            columns='account_description',  # Use the new concatenated column
            values='value',
            aggfunc='sum',
            fill_value=0  # Replace missing values with 0
        ).reset_index()

        # print("Pivoted DataFrame created successfully.")
        df.to_csv('df.csv', index=False)
        pivot_df.to_csv('pivot_df.csv', index=False)
        pivot_df2.to_csv('pivot_df2.csv', index=False)

        # Step 2: Calculate the Indicators
        for indicator in indicator_list:
            column_description = indicator['description']
            column_account = indicator['account']
            formula = indicator['formula']

            try:
                # Apply the formula
                # pivot_df[column_description] = formula(pivot_df)
                pivot_df[column_account] = formula(pivot_df)

                # print(f"Indicator '{column_account} - {column_description}' calculated successfully.")

            except KeyError as e:
                print(f"'KeyError {column_account} - {column_description}': {e}")
                pivot_df[column_account] = np.nan  # Assign NaN if any required account is missing
            except Exception as e:
                print(f"Error calculating the indicator '{column_account} - {column_description}': {e}")
                pivot_df[column_account] = np.nan  # Assign NaN in case of other errors

        # Step 3: Create New Rows for the Indicators
        new_rows = []

        for indicator in indicator_list:
            column_account = indicator['account']
            column_description = indicator['description']

            if column_account not in pivot_df.columns:
            # if description not in pivot_df.columns:
                print(f"Indicator '{column_account} - {column_description}' was not calculated and will be ignored.")
                continue

            # Extract the calculated values for the indicator
            indicator_values = pivot_df[['company_name', 'type', 'quarter', column_account]].copy()
            indicator_values.rename(columns={column_account: 'value'}, inplace=True)
            # indicator_values = pivot_df[['company_name', 'type', 'quarter', column_description]].copy()
            # indicator_values.rename(columns={column_description: 'value'}, inplace=True)

            indicator_values['account'] = column_account
            indicator_values['description'] = column_description

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

        # print(f'{frame_name} incorporated into {sector}')
        return updated_df

    def main(self):
        """
        Run the financial ratios calculation using the main thread.
        """
        dfs = {}
        try:
            dict_df = self.load_data(settings.markets_file)

            # Define the dictionary with the indicator names and their corresponding values
            indicators = {
                'Relações Entre Ativos e Passivos': intel.indicators_11,
                'Patrimônio': intel.indicators_11b,
                'Dívida': intel.indicators_12,
                'Resultados Fundamentalistas 1': intel.indicators_13,
                'Resultados Fundamentalistas 2': intel.indicators_14,
                'Resultados Fundamentalistas 3': intel.indicators_15,
                'Resultados Fundamentalistas 4': intel.indicators_16,
                'Fluxo de Caixa': intel.indicators_17,
                'Valor Agregado': intel.indicators_18,
                'Preço e Lucro por Ação': intel.indicators_21,
                'Crescimento e PEG': intel.indicators_22,
                'Dividendos e TSR': intel.indicators_23,
                'Múltiplos de Valuation': intel.indicators_24,
                'Fluxo de Caixa Livre e P/FC': intel.indicators_25
            }

            start_time = time.time()
            for i, (sector, df) in enumerate(dict_df.items()):
                df = self.adjust_dfs_types(df)

                # Loop through the dictionary and apply the add_indicators method
                start_time2 = time.time()
                for j, (key, value) in enumerate(indicators.items()):

                    df = self.add_indicators(df, key, value, sector)

                    extra_info2 = [sector, key]
                    system.print_info(j, len(indicators), start_time2, extra_info2)

                df.to_csv(f'{sector}_ratios.csv', index=False)
                dfs[sector] = df

                dfs = self.save_to_db(sector, df)
                
                extra_info = [sector]
                system.print_info(i, len(dict_df), start_time, extra_info)

        except Exception as e:
            system.log_error(f"Error initializing MinancialRatios: {e}")

        return dfs
    
if __name__ == "__main__":
    financial_ratios = FinancialRatios()
    financial_ratios.main()
