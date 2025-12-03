import os
import sqlite3
import time
import warnings
from threading import Lock

import numpy as np
import pandas as pd
import urllib3

from utils.base_processor import BaseProcessor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")
pd.set_option("future.no_silent_downcasting", True)


class EventsStatementsProcessor(BaseProcessor):
    """definitions."""

    def __init__(self):
        """definitions."""
        super().__init__()
        self.db_lock = Lock()  # Initialize a threading Lock

        # Initialize database and table names
        self.tbl_company_info = self.config.databases["raw"]["table"]["company_info"]
        self.tbl_statements_corp_events = self.config.databases["raw"]["table"]["statements_corp_events"]
        self.tbl_statements_normalized = self.config.databases["raw"]["table"]["statements_normalized"]

        self.tbl_stock_data = self.config.databases["raw"]["table"]["stock_data"]

        self.statements_version_delimiter = self.config.domain["statements_version_delimiter"]

        self.db_filepath = self.config.databases["raw"]["filepath"]

    def process_instance(self, sub_batch, payload, progress):
        """Process a single batch by delegating to process_batch."""
        result = pd.DataFrame()  # Return an empty DataFrame on failure

        try:
            print(
                f"Starting batch {progress['batch_index']+1}/{progress['total_batches']} {100 * (progress['batch_index']+1) / progress['total_batches']:.02f}%"
            )
            batch_processor = EventsStatementsProcessor()

            # Delegate to process_batch for the actual batch processing
            result, benchmark_results = batch_processor.benchmark_function(
                batch_processor.process_batch, sub_batch, payload, progress, benchmark_mode=False
            )

            # Save result to database
            self.save_to_db(dataframe=result, table_name=self.tbl_statements_corp_events, db_filepath=self.db_filepath)

        except Exception as e:
            self.log_error(f"Error in process_instance: {e}")

        return result

    def process_batch(self, sub_batch, payload, progress):
        """Process a batch of financial data by iterating over rows and
        scraping statements."""
        try:
            dfs = []

            # loop companies, load stock_market data and statements_data per company
            start_time = time.monotonic()
            for i, (ii, row) in enumerate(sub_batch.iterrows()):
                ticker = row["ticker"]
                ticker_code = row["ticker_code"]
                company_name = row["company_name"]

                statements_company, stock_data, stock_splits = self.get_company_financials(
                    payload, company_name, ticker_code
                )

                if not statements_company.empty:
                    # get stock items
                    statements_stocks = statements_company[
                        statements_company["account"].str.startswith(self.config.domain["stock_prefix"])
                    ]
                    stocks = self.process_financial_data(stock_data, stock_splits, statements_stocks)

                    for group_type in ["DFs Individuais", "DFs Consolidadas"]:
                        group_statements = statements_company[statements_company["type"] == group_type]

                        if not group_statements.empty:
                            group_stocks = self.process_financial_data(stock_data, stock_splits, group_statements)

                            df = pd.concat([stock_data, stocks, group_stocks], axis=1).loc[
                                :, ~pd.concat([stock_data, stocks, group_stocks], axis=1).columns.duplicated()
                            ]

                        else:
                            df = stocks
                            df = pd.concat([stock_data, stocks], axis=1).loc[
                                :, ~pd.concat([stock_data, stocks], axis=1).columns.duplicated()
                            ]

                        df["ticker_code"] = ticker_code
                        df["group_type"] = group_type

                        # Reorganizar as colunas para que 'ticker_code' e 'group_type' sejam as primeiras
                        columns_order = ["ticker_code", "group_type"] + [
                            col for col in df.columns if col not in ["ticker_code", "group_type"]
                        ]
                        df = df[columns_order]
                        dfs.append(df)

                total_progress = f"{((progress['batch_start'] + i) / progress['scrape_size']) * 100:.2f}%"
                global_unit = progress["batch_start"] + i
                progress_info = f"({global_unit}+{progress['scrape_size'] - global_unit} {progress['thread_id']})"
                extra_info = [progress_info, i + 1, ticker_code, company_name]
                self.print_info(i, len(sub_batch), start_time, extra_info)

            # Concatenar todos os DataFrames
            if dfs:
                result = pd.concat(dfs, ignore_index=True)

        except Exception as e:
            self.log_error(e)
            result = pd.DataFrame

        return result

    def get_targets(self, company_info):
        """Obtém os alvos de raspagem de dados para a empresa.

        Esta função expande as informações da empresa e retorna os alvos específicos para a raspagem.

        Parâmetros:
        - company_info (pd.DataFrame): DataFrame contendo informações das empresas.

        Retorna:
        - pd.DataFrame: Um DataFrame contendo os alvos de raspagem.
        """
        try:
            # Expande a lista de empresas e seus respectivos alvos para raspagem
            targets = self.explode_company(company_info).reset_index(drop=True)

        except Exception as e:
            # Registra qualquer erro ocorrido
            self.log_error(e)
            targets = pd.DataFrame()

        return targets

    def get_company_financials(self, payload, company_name, ticker_code=None):
        """Obtém as demonstrações financeiras e os dados históricos de ações de
        uma empresa.

        Esta função carrega e processa os dados financeiros padronizados da empresa,
        filtrando os dados mais recentes por trimestre e organizando-os. Também busca
        os preços históricos de ações da empresa com base no código do ticker.

        Parâmetros:
        - company_name (str): Nome da empresa cujas demonstrações financeiras serão extraídas.
        - ticker_code (str, opcional): Código do ticker da empresa. Se não for fornecido, usa um alternativo.

        Retorna:
        - statements_company (pd.DataFrame): DataFrame contendo as demonstrações financeiras organizadas.
        - company_stock_data (pd.DataFrame): DataFrame contendo os dados históricos de ações.
        - splits (pd.DataFrame): DataFrame contendo os eventos de desdobramento de ações.
        """
        try:
            # Obter Demonstrações Financeiras
            statements_company = self._get_company_statements(payload, company_name)

            # Obter Dados Históricos de Ações
            company_stock_data, splits = self._get_company_stock_data(payload, ticker_code)

        except Exception as e:
            self.log_error(e)
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        return statements_company, company_stock_data, splits

    def _get_company_statements(self, payload, company_name):
        """Obtém as demonstrações financeiras de uma empresa e filtra os dados
        mais recentes.

        Retorna:
        - pd.DataFrame: DataFrame contendo as demonstrações financeiras organizadas.
        """
        try:
            param = "company_name"
            sql_company = f"SELECT * FROM {self.tbl_statements_normalized} WHERE {param} = ?"
            standart_statements = self.load_data(
                query=sql_company, params=(company_name,), db_filepath=self.db_filepath, alert=False
            )

            final_df = standart_statements.loc[
                standart_statements.groupby(self.statements_version_delimiter)["version"].idxmax()
            ]
            final_df["quarter"] = pd.to_datetime(final_df["quarter"])

            return final_df

        except Exception as e:
            self.log_error(e)
            return pd.DataFrame()

    def _get_ticker_alternative(self):
        """description."""
        ticker = ""
        try:
            # Query SQL para encontrar o ticker com o maior range de date
            query = """
            SELECT ticker_code, 
                MIN(date) AS min_date, 
                MAX(date) AS max_date, 
                (JULIANDAY(MAX(date)) - JULIANDAY(MIN(date))) AS date_range
            FROM tbl_stock_data
            GROUP BY ticker_code
            ORDER BY date_range DESC
            LIMIT 1;
            """
            with sqlite3.connect(self.db_filepath) as conn:
                df = pd.read_sql_query(query, conn)
                ticker_code = df["ticker_code"].iloc[0]

        except Exception as e:
            self.log_error(e)

        return ticker_code

    def _get_company_stock_data(self, payload, ticker_code=None):
        """Obtém os dados históricos de ações de uma empresa específica.

        Retorna:
        - pd.DataFrame: DataFrame contendo os dados históricos de ações.
        """
        try:
            # Consulta SQL para obter os dados históricos de ações de um ticker específico de uma empresa específica
            param = "ticker_code"
            sql_stock_data = f"SELECT * FROM {self.tbl_stock_data} WHERE {param} = ?"

            tk_cd = ticker_code if ticker_code is not None else self._get_ticker_alternative()

            company_stock_data = self.load_data(
                query=sql_stock_data, params=(tk_cd,), db_filepath=self.db_filepath, alert=False
            )

            try:
                # Remove linhas onde a data esteja ausente
                company_stock_data = company_stock_data.dropna(subset=["date"])

                # Converte a coluna 'date' para formato datetime para garantir consistência
                company_stock_data["date"] = pd.to_datetime(company_stock_data["date"])
            except:
                pass

            if not company_stock_data.empty:
                if ticker_code != None:
                    splits = company_stock_data[
                        ["company_name", "ticker", "ticker_code", "date", "stock_splits"]
                    ].query("stock_splits != 0")
                    splits["date"] = pd.to_datetime(splits["date"])
                else:
                    company_stock_data = company_stock_data[["date"]].copy()
                    required_columns = ["close", "dividends", "high", "low", "open", "stock_splits", "volume"]
                    company_stock_data = company_stock_data.reindex(
                        columns=["date"] + required_columns, fill_value=np.nan
                    )
                    splits = pd.DataFrame(columns=["company_name", "ticker", "ticker_code", "date", "stock_splits"])
                    splits["date"] = pd.to_datetime(splits["date"])
            else:
                company_stock_data, splits = self._get_company_stock_data(payload)
                splits = pd.DataFrame(columns=self.config.domain["split_columns"])

        except Exception as e:
            self.log_error(e)
            company_stock_data = pd.DataFrame()
            splits = pd.DataFrame(columns=self.config.domain["split_columns"])

        return company_stock_data, splits

    def _get_stock_splits(self, company_stock_data, ticker_code=None):
        """Obtém os eventos de desdobramento de ações de uma empresa.

        Retorna:
        - pd.DataFrame: DataFrame contendo os eventos de desdobramento de ações.
        """
        try:
            if ticker_code:
                splits = company_stock_data[["company_name", "ticker", "ticker_code", "date", "stock_splits"]].query(
                    "stock_splits != 0"
                )
                splits["date"] = pd.to_datetime(splits["date"])
            else:
                required_columns = ["close", "dividends", "high", "low", "open", "stock_splits", "volume"]
                company_stock_data = company_stock_data[["date"]].copy()
                company_stock_data = company_stock_data.reindex(columns=["date"] + required_columns, fill_value=np.nan)
                splits = pd.DataFrame(columns=["company_name", "ticker", "ticker_code", "date", "stock_splits"])
                splits["date"] = pd.to_datetime(splits["date"])

            return splits

        except Exception as e:
            self.log_error(e)
            return pd.DataFrame()

    def process_financial_data(self, stock_data, stock_splits, statements):
        """definitions."""
        try:
            statements_quarterly = self._get_statements_quarterly(statements)

            statements_daily = self._parse_statements_daily(statements_quarterly, stock_data)

            columns_to_update = [
                col for col in statements_quarterly.columns if col.startswith(self.config.domain["stock_prefix"])
            ]

            stocks = self._parse_statements_filled(
                statements_quarterly, statements_daily, stock_splits, columns_to_update=columns_to_update
            )

        except Exception as e:
            self.log_error(e)

        return stocks

    def _get_statements_quarterly(self, statements):
        """definitions."""
        index_columns = self.config.domain["statements_index_columns"]
        pivot_columns = self.config.domain["statements_pivot_columns"]

        try:
            # Cria uma tabela pivô para organizar os dados financeiros
            statements_quarterly = statements.pivot_table(
                index=index_columns,  # Define as colunas principais como índice
                columns=pivot_columns,  # Define as colunas a serem pivotadas
                values="value",  # Usa os valores financeiros como dados
                aggfunc="first",  # Usa 'first' para lidar com duplicatas
            ).reset_index()

            # Ajusta os nomes das colunas para um formato mais acessível
            statements_quarterly.columns = [
                (
                    self.config.domain["sep_dash"].join([str(part) for part in col if part])
                    if isinstance(col, tuple)
                    else col
                )
                for col in statements_quarterly.columns
            ]

        except Exception as e:
            self.log_error(e)

        return statements_quarterly

    def _parse_statements_daily(self, statements_quarterly, company_stock_data):
        """Alinha as demonstrações financeiras trimestrais com os dados diários
        das ações.

        Esta função expande os dados das demonstrações financeiras trimestrais para corresponder
        às datas dos preços diários das ações, garantindo que os dados financeiros estejam
        disponíveis para cada dia de negociação.

        Parâmetros:
        - statements (pd.DataFrame): DataFrame contendo demonstrações financeiras trimestrais.
        - company_stock_data (pd.DataFrame): DataFrame contendo dados diários de preços das ações.

        Retorna:
        - pd.DataFrame: Um DataFrame onde cada linha diária está alinhada com a demonstração trimestral mais próxima.
        """
        try:
            # Extrai datas diárias únicas do stock_data para garantir o alinhamento
            daily_dates = company_stock_data[["date"]].drop_duplicates()

            # Mescla os dados diários das ações com as demonstrações trimestrais, alinhando as datas dos trimestres
            statements_daily = pd.merge(
                daily_dates, statements_quarterly, left_on="date", right_on="quarter", how="left"
            )

            # Converte colunas de datas para formato datetime para garantir ordenação e processamento adequados
            statements_daily["date"] = pd.to_datetime(statements_daily["date"], errors="coerce")
            statements_daily["quarter"] = pd.to_datetime(statements_daily["quarter"], errors="coerce")

            # Ordena por data para garantir que o preenchimento posterior aconteça corretamente
            statements_daily = statements_daily.sort_values(by="date")

        except Exception as e:
            # Em caso de erro, retorna um DataFrame vazio e registra o erro
            statements_daily = pd.DataFrame()
            self.log_error(e)

        return statements_daily

    def _parse_statements_filled(self, statements_quaterly, statements_daily, splits, columns_to_update):
        """Processa e preenche os dados financeiros diários alinhados com os
        dados das ações.

        Esta função realiza:
        - **Preenchimento de valores ausentes (Backfilling):** Garante que os dados financeiros diários
          carreguem a última informação trimestral disponível.
        - **Ajustes para Desdobramentos de Ações (Stock Splits):** Ajusta os dados financeiros para
          eventos de desdobramento de ações dentro de cada trimestre.
        - **Controle Trimestral:** Garante que os dados financeiros de cada trimestre sejam preservados
          e corretamente alinhados com os dias de negociação.

        Parâmetros:
        - statements (pd.DataFrame): DataFrame original contendo as demonstrações financeiras trimestrais.
        - statements_daily (pd.DataFrame): DataFrame com os dados financeiros alinhados aos preços diários das ações.
        - splits (pd.DataFrame): DataFrame contendo eventos de desdobramento de ações e suas respectivas datas-ex.
        - columns_to_update (list, opcional): Colunas específicas a serem atualizadas; por padrão, todas as colunas financeiras.

        Retorna:
        - pd.DataFrame: DataFrame preenchido e ajustado para os desdobramentos de ações.
        """
        try:
            # Cria uma cópia dos dados diários para evitar modificar o DataFrame original
            statements_daily_filled = statements_daily.copy()

            # Gera uma coluna que acompanha o último dia do trimestre correspondente para cada data
            statements_daily_filled["date_quarter"] = (
                statements_daily_filled["date"].dt.to_period("Q").dt.end_time.dt.normalize()
            )

            # Extrai os trimestres únicos para iteração
            unique_quarters = statements_daily_filled["date_quarter"].unique()

            # Dicionário para armazenar os dados processados de cada trimestre
            filled_list = {}
            last_quarter_values = None  # Armazena os últimos valores conhecidos do trimestre anterior

            # Itera sobre cada trimestre único e processa seus dados financeiros
            for quarter in unique_quarters:
                if pd.notna(quarter):  # Garante que o trimestre seja válido (não seja NaT)
                    # Seleciona as linhas pertencentes ao trimestre atual
                    mask = statements_daily_filled["date_quarter"] == quarter
                    quarter_data = statements_daily_filled.loc[mask].copy()  # Copia para evitar modificar o original

                    # Aplica preenchimento para garantir continuidade dos valores dentro do trimestre
                    quarter_data = quarter_data.bfill().infer_objects(copy=False)

                    # Identifica os eventos de desdobramento de ações dentro deste trimestre
                    split_mask = (splits["date"] >= quarter_data["date"].min()) & (
                        splits["date"] <= quarter_data["date"].max()
                    )
                    quarter_splits = splits.loc[split_mask]

                    # Processa cada evento de desdobramento encontrado no trimestre
                    for _, split_row in quarter_splits.iterrows():
                        split_date = split_row["date"]  # Data em que ocorre o desdobramento (Data-Ex)
                        split_factor = split_row["stock_splits"]  # Fator de multiplicação do ajuste

                        # Identifica as linhas ANTES da data-ex → Aplica os valores do trimestre anterior ou divide
                        before_split_mask = quarter_data["date"] < split_date

                        # Se houver valores conhecidos do trimestre anterior, aplica-os diretamente
                        if last_quarter_values is not None:
                            quarter_data.loc[before_split_mask, columns_to_update] = last_quarter_values.values
                        else:
                            # Se não houver valores anteriores, divide pelo fator de desdobramento como fallback
                            adjusted_values = quarter_data.loc[before_split_mask, columns_to_update] / split_factor

                            # Substituir valores infinitos por NaN para evitar erro na conversão
                            adjusted_values = adjusted_values.replace([np.inf, -np.inf], np.nan)

                            # Preencher NaN com 0 antes de converter para inteiro
                            adjusted_values = adjusted_values.fillna(0).round(2).astype(int)

                            # Aplicar valores corrigidos ao DataFrame
                            quarter_data.loc[before_split_mask, columns_to_update] = adjusted_values

                    # Armazena os últimos valores do trimestre atual para usar no próximo trimestre
                    last_quarter_values = quarter_data[columns_to_update].iloc[-1]

                    # Remove a coluna 'date_quarter' antes de consolidar os dados do trimestre
                    quarter_data = quarter_data.drop(columns=["date_quarter"], errors="ignore")

                    # Armazena os dados do trimestre processado no dicionário
                    filled_list[quarter] = quarter_data

            # Concatena todos os dados processados dos trimestres em um único DataFrame
            try:
                result = pd.concat(filled_list).sort_values(by="date").reset_index(drop=True)
            except Exception:
                result = pd.DataFrame(columns=self.config.domain["statements_columns_empty_df"])

        except Exception as e:
            # Registra qualquer erro e retorna um DataFrame vazio
            self.log_error(e)
            result = pd.DataFrame()

        return result

    def reset_and_save_db(self, table_name, db_filepath, df):
        """Deletes the existing database, recreates it, creates a table based
        on final_df, and saves data.

        Args:
            db_filepath (str): Path to the SQLite database.
            table_name (str): Name of the table to create.
            final_df (DataFrame): DataFrame containing the data to save.
        """
        try:
            # Step 1: Delete existing database file
            if os.path.exists(db_filepath):
                os.remove(db_filepath)

            # Step 2: Create a new database and define schema dynamically
            conn = sqlite3.connect(db_filepath)
            cursor = conn.cursor()

            # Generate SQL for table creation based on DataFrame columns
            column_definitions = ", ".join([
                (f'"{col}" REAL' if df[col].dtype in ["float64", "int64"] else f'"{col}" TEXT') for col in df.columns
            ])

            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {column_definitions}
            )
            """

            cursor.execute(create_table_sql)
            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.print_info(e)
            return False

    def main(self, thread=True):
        """definitions."""
        try:
            # # Carregar dados processados anteriormente
            # standart_statements = self.load_data(
            #     table_name=self.tbl_statements_normalized, db_filepath=self.db_filepath
            # )
            # standart_statements = standart_statements.loc[standart_statements.groupby(self.statements_version_delimiter)['version'].idxmax()]

            # load existing company_info data
            company_info = self.load_data(table_name=self.tbl_company_info, db_filepath=self.db_filepath)
            statements_corp_events = self.load_data(
                table_name=self.tbl_statements_corp_events, db_filepath=self.db_filepath
            )
            # standart_statements = statements_corp_events = pd.DataFrame()
            targets = self.get_targets(company_info)

            # Exit if no targets
            if targets.empty:
                self.db_optimize(self.config.databases["raw"]["filepath"])
                return True

            # Process targets using threading or sequential logic
            # payload = {"standart_statements": standart_statements, "statements_corp_events": statements_corp_events}
            payload={}
            result = self.run(
                targets,
                payload=payload,
                thread=thread,
                module_name=self.inspect.getmodule(self.inspect.currentframe()).__name__,
            )

            # Save processed data
            if not result.empty:
                self.save_to_db(
                    dataframe=result, table_name=self.tbl_statements_corp_events, db_filepath=self.db_filepath
                )

        except Exception as e:
            self.log_error(f"Error in main: {e}")

        return True
