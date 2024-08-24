import time
import os
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

    def load_data(self, files):
        """
        Load financial data from the database.

        Args:
            files (str): The type of data file to load (e.g., 'statements', 'math').

        Returns:
            dict: A dictionary where keys are sectors and values are DataFrames containing the NSD data for that sector.
        """
        try:
            # Construct the path to the database
            db_file = os.path.join(self.db_folder, f"{settings.db_name.split('.')[0]} {files}.db")
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Query to get all table names, excluding internal SQLite tables like sqlite_stat1
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()

            dfs = {}  # Initialize the dictionary to store sector DataFrames
            start_time = time.time()  # Initialize the start time to measure progress
            total_lines = 0
            # Iterate over each table to load data
            for i, table in enumerate(tables):
                sector = table[0]
                df = pd.read_sql_query(f"SELECT * FROM {sector}", conn)

                # Remove rows where 'account' is empty
                df = df[df['account'].notna() & df['account'].str.strip().astype(bool)]

                # Normalize date columns to datetime format
                df['quarter'] = pd.to_datetime(df['quarter'], errors='coerce')  # Convert to datetime format

                # Normalize numeric columns
                df['value'] = pd.to_numeric(df['value'], errors='coerce')  # Converte para numérico, colocando NaN onde não for possível

                df, _ = self.filter_newer_versions(df)
                dfs[sector] = df  # Store the DataFrame with the sector as the key
                
                # Use system.print_info to display progress
                lines = len(df)
                total_lines += lines
                extra_info = [f'{lines} lines in', sector, f'{total_lines} total lines']
                system.print_info(i, extra_info, start_time, total_size=len(tables))

            return dfs

        except Exception as e:
            system.log_error(f"Error loading data from {files} database: {e}")
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
            # Sort the DataFrame by group_columns and version in descending order
            df_sorted = df.sort_values(by=group_columns + [version_column], ascending=[True] * len(group_columns) + [False])
            
            # Drop duplicates based on the specified group_columns, keeping only the first (newest) entry
            df_filtered = df_sorted.drop_duplicates(subset=group_columns, keep='first')

            # Identify duplicate entries that are not the newest (i.e., the remaining entries after filtering)
            df_dup = df_sorted[~df_sorted.index.isin(df_filtered.index)]

            return df_filtered, df_dup

        except Exception as e:
            system.log_error(f"Error during filtering newer versions: {e}")
            return pd.DataFrame(columns=settings.statements_columns)

    def filter_new_entries(self, dict_new, dict_existing):
        """
        Filter out new entries in dict_new that are not present in dict_existing.

        Args:
            dict_new (dict): A dictionary where keys are sectors and values are DataFrames containing the latest data.
            dict_existing (dict): A dictionary where keys are sectors and values are DataFrames containing already processed data.

        Returns:
            dict: A dictionary where keys are sectors and values are DataFrames with entries in dict_new that are not present in dict_existing.
        """
        key_columns = ['company_name', 'quarter', 'type', 'frame', 'account']
        new_entries_column = 'version'

        filtered_results = {}  # Dictionary to store the filtered results
        start_time = time.time()  # Initialize the start time to measure progress
        total_sectors = len(dict_new)  # Total number of sectors to be processed

        try:
            # Iterate over each sector in the new dictionary
            for i, (sector, df_new) in enumerate(dict_new.items()):
                if sector in dict_existing:
                    # Get the existing DataFrame for the same sector
                    df_existing = dict_existing[sector]

                    # Perform an outer join on key columns to identify new or different entries
                    df_comparison = pd.merge(df_new, df_existing[key_columns], on=key_columns, how='outer', indicator=True)

                    # Condição 1: Manter todas as linhas que estão apenas no df_new ('left_only')
                    df_left_only = df_comparison[df_comparison['_merge'] == 'left_only']

                    # Condição 2: Para entradas que estão em 'both', manter apenas a linha com a versão maior para cada grupo de duplicatas
                    df_both = df_comparison[df_comparison['_merge'] == 'both'].copy()

                    # Identificar duplicatas e verificar diferenças de versão
                    # Para 'both', precisamos comparar versões e manter apenas a versão mais alta
                    df_both = df_both.sort_values(by=key_columns + [new_entries_column], ascending=[True] * len(key_columns) + [False])

                    # Manter apenas duplicatas com versões diferentes
                    df_both = df_both.drop_duplicates(subset=key_columns, keep='first')

                    # Remover entradas do df_both que já existem no df_existing
                    df_both = df_both[~df_both.set_index(key_columns).index.isin(df_existing.set_index(key_columns).index)]

                    # Combinar resultados das duas condições
                    df_filtered = pd.concat([df_left_only, df_both], ignore_index=True)
                    size = len(df_filtered)

                    # Add the filtered DataFrame to the results dictionary
                    if not df_filtered.empty:
                        filtered_results[sector] = df_filtered
                else:
                    # If the sector is not in the existing dictionary, consider all entries as new
                    filtered_results[sector] = df_new
                    size = len(df_new)

                # Prepare extra information for print_info
                extra_info = [size, sector]

                # Call system.print_info to display progress
                system.print_info(i, extra_info, start_time, total_sectors)

            return filtered_results

        except Exception as e:
            system.log_error(f"Error filtering new entries: {e}")
            return {}

    def save_to_db(self, dict_math):
        """
        Save transformed data to a new database (e.g., b3 {math}.db) with each sector as a table.

        Args:
            dict_math (dict): A dictionary where keys are sectors and values are DataFrames containing the transformed data.
        """
        try:
            # Construct the path to the new database
            db_path = os.path.join(self.db_folder, f"{settings.db_name.split('.')[0]} {settings.statements_file_math}.db")
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                for sector, df in dict_math.items():
                    # Ordenar os dados de acordo com settings.statements_order
                    df = df.sort_values(by=settings.statements_order)

                    # Verificar se a tabela existe
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{sector}';")
                    table_exists = cursor.fetchone() is not None

                    if table_exists:
                        # Atualizar registros existentes e inserir novos
                        for _, row in df.iterrows():
                            placeholders = ', '.join(['?'] * len(row))
                            columns = ', '.join(row.index)
                            update_set = ', '.join([f"{col}=excluded.{col}" for col in row.index])

                            insert_sql = f"""
                            INSERT INTO {sector} ({columns}) 
                            VALUES ({placeholders}) 
                            ON CONFLICT (company_name, quarter, version, type, frame, account) 
                            DO UPDATE SET {update_set};
                            """
                            cursor.execute(insert_sql, tuple(row))
                    else:
                        # Criar a tabela e inserir todos os dados transformados
                        df.to_sql(sector, conn, if_exists='replace', index=False)

                    # Log ou imprimir progresso de salvamento
                    print(f"Dados transformados salvos para o setor: {sector} no banco de dados: {db_path}")

                # Commit para garantir que todas as mudanças sejam salvas
                conn.commit()

        except Exception as e:
            system.log_error(f"Erro ao salvar dados no banco de dados: {e}")

    def mathmagic(self, dict_df):
        """
        Perform math transformations on each DataFrame in the dictionary sequentially.

        Args:
            dict_df (dict): A dictionary where keys are sectors and values are DataFrames containing the filtered data to process.

        Returns:
            dict: A dictionary where keys are sectors and values are DataFrames with transformed data.
        """
        transformed_results = {}  # Dictionary to store the transformed DataFrames
        start_time = time.time()  # Initialize the start time to measure progress
        total_sectors = len(dict_df)  # Total number of sectors to process

        for i, (sector, df) in enumerate(dict_df.items()):
            try:
                # Ensure 'quarter' is in datetime format and create 'year' and 'month' columns
                df['quarter'] = pd.to_datetime(df['quarter'], errors='coerce')
                df['year'] = df['quarter'].dt.year  # Create the 'year' column
                df['month'] = df['quarter'].dt.month  # Create the 'month' column

                # Step 3: Split into groups
                unmodified_statements, year_end_balance_statements, cumulative_quarter_balances_statements = self.split_into_groups(df)

                # Step 4: Apply the adjustments
                year_end_balance_statements = self.adjust_year_end_balance(year_end_balance_statements)
                cumulative_quarter_balances_statements = self.adjust_cumulative_quarter_balances(cumulative_quarter_balances_statements)

                # Step 5: Combine all groups back together
                df_transformed = pd.concat([unmodified_statements, year_end_balance_statements, cumulative_quarter_balances_statements])
                df_transformed.drop(columns=['year', 'month'], inplace=True)

                # Sort values
                df_transformed = df_transformed.sort_values(by=settings.statements_order)

                # Store the transformed DataFrame in the results dictionary
                transformed_results[sector] = df_transformed

                # Prepare extra information for print_info
                extra_info = [f'{len(df_transformed)} {sector}']
                
                # Call system.print_info to display progress
                system.print_info(i, extra_info, start_time, total_sectors)

            except Exception as e:
                system.log_error(f"Error processing sector {sector}: {e}")
                continue  # Skip to the next sector in case of error

        return transformed_results

    def main_sequential(self, dict_statements, dict_math):
        """
        Run the math transformations on each database file sequentially.

        Args:
            dict_statements (dict): Dicionário contendo os dados originais atualizados.
            dict_math (dict): Dicionário contendo os dados já processados.
        """
        try:
            # Passo 2: Comparar registros de cada setor
            dict_filtered = self.filter_new_entries(dict_statements, dict_math)

            # Passo 4: Aplicar Transformações Matemáticas
            dict_transformed = self.mathmagic(dict_filtered)

            # Passo 5: Salvar Dados Transformados no Banco de Dados
            self.save_to_db(dict_transformed)

            return dict_transformed

        except Exception as e:
            system.log_error(f"Erro durante o processamento sequencial: {e}")
            return {}

    def main(self, thread=False):
        """
        Main function to run the math transformations either sequentially or using multiple threads.
        
        Args:
            thread (bool): Flag to determine whether to run in thread mode or sequential mode.
        """
        # load statements and math
        dict_statements = self.load_data(settings.statements_file)
        dict_math = self.load_data(settings.statements_file_math)

        if thread:
            # Run the thread processing logic
            self.main_thread()
        else:
            # Run the sequential processing logic
            self.main_sequential(dict_statements, dict_math)

if __name__ == "__main__":
    transformer = MathTransformation()
    transformer.main(thread=False)
