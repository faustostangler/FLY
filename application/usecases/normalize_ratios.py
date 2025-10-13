from typing import Any, List

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow, UowFactoryPort
from domain.dtos.indicators_dto import IndicatorsDTO
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
from infrastructure.utils.list_flatenner import ListFlattener

import pandas as pd

# from infrastructure.helpers.list_flattener import ListFlattener


class NormalizeUseCase:
    """Use case for synchronizing data between scraper and repository."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,

        repository_company: RepositoryCompanyDataPort,
        repository_stock_quote: RepositoryStockQuotePort,
        repository_indicators: RepositoryIndicatorsPort,
        repository_statements_fetched: RepositoryStatementFetchedPort,

        uow_factory: UowFactoryPort,

        max_workers: int = 1,
    ):
        """Initialize the use case with its dependencies.

        Args:
            config (ConfigPort): Application configuration provider.
            logger (LoggerPort): Logger interface for capturing messages.
            repository (RepositoryCompanyDataPort): Repository for persisting company data.
            scraper (ScraperCompanyDataPort): Scraper used to fetch company data.
            max_workers (int, optional): Maximum number of workers for parallel execution.
                Defaults to 1, or falls back to the value in the config worker pool.
        """
        self.config = config
        self.logger = logger
        self.repository_company = repository_company
        self.repository_stock_quote = repository_stock_quote
        self.repository_indicators = repository_indicators
        self.repository_statements_fetched = repository_statements_fetched

        self.uow_factory = uow_factory

        self.max_workers = max_workers or (self.config.worker_pool.max_workers or 1)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.run()

    def run(self) -> SyncResultsDTO:
        """Run the full synchronization pipeline.

        Steps:
            1. Retrieve company data from the scraper.
            2. Transform results into ``CompanyDataDTO`` objects.
            3. Save them into the repository in batches.

        Returns:
            SyncCompanyDataResultDTO: Summary of the synchronization process,
            including counts and network usage metrics.
        """
        # Collect company identifiers already stored in the repository
        with self.uow_factory() as uow:
            try:
                indicators_df = self._load_indicators(uow=uow)
                indicators_df.to_csv("df_indicators.csv")
                indicator_matrices = self._prepare_indicator_matrices(indicators_df)

                companies = [company for (company,) in self.repository_company.iter_existing_by_columns("company_name", uow=uow)]
                if not companies:
                    return SyncResultsDTO(items=[], metrics=0)
                for company_name in companies:
                    if company_name == "ALPARGATAS SA":
                        rows = self.repository_company.get_by_column_values(values=[("company_name", company_name)], uow=uow)
                        ticker_codes:List = next((row.ticker_codes for row in rows if row.company_name == company_name),[],)
                        statements_df = self._load_statements(company_name=company_name, uow=uow)
                        statements_df.to_csv(f"df_statements_{company_name}.csv")

                        dfs = self._split_statements(statements_df)

                        quotes_df = self._load_quotes(ticker_codes=ticker_codes, uow=uow)
                        quotes_df.to_csv(f"df_quotes_{company_name}.csv")

            except Exception as e:
                self.logger.log(f"NormalizeUseCase failed: {e}", level="error")
                raise

    def _load_indicators(self, uow: Uow) -> pd.DataFrame:
        rows = self.repository_indicators.get_all(uow=uow)
        if not rows:
            from sqlalchemy.inspection import inspect
            model, _ = self.repository_indicators.get_model_class()
            columns = [c.key for c in inspect(model).mapper.column_attrs]
            return pd.DataFrame(columns=columns)

        indicators = pd.DataFrame(rows)
        indicators["date"] = pd.to_datetime(indicators["date"], errors="coerce")
        indicators["value"] = pd.to_numeric(indicators["value"], errors="coerce")
        indicators.sort_values(["code", "name", "date"], inplace=True)
        return indicators.dropna(subset=["date"]).reset_index(drop=True)

    def _prepare_indicator_matrices(
        self, indicators: pd.DataFrame
    ) -> dict[str, pd.DataFrame]:
        matrices: dict[str, pd.DataFrame] = {}
        if indicators.empty:
            return matrices

        for (source, code), group in indicators.groupby(["source", "code"]):
            pivot = (
                group.pivot_table(
                    index="date",
                    columns="name",
                    values="value",
                    aggfunc="last",
                )
                .sort_index()
            )
            matrices[str(code)] = pivot
            pivot.to_csv(f"df_indicator_{source}_{str(code)}.csv")

        return matrices

    def _load_statements(self, company_name:str, uow: Uow) -> pd.DataFrame:
        rows = self.repository_statements_fetched.get_by_column_values(values=[("company_name", company_name)], uow=uow)
        if not rows:
            from sqlalchemy.inspection import inspect
            model, _ = self.repository_statements_fetched.get_model_class()
            columns = [c.key for c in inspect(model).mapper.column_attrs]
            return pd.DataFrame(columns=columns)

        statements = pd.DataFrame(rows)
        statements["quarter"] = pd.to_datetime(statements["quarter"], errors="coerce")
        statements["value"] = pd.to_numeric(statements["value"], errors="coerce")
        statements["version_numeric"] = pd.to_numeric(statements["version"], errors="coerce").fillna(-1)
        statements.sort_values(["company_name", "quarter", "version_numeric"], inplace=True)
        return statements.dropna(subset=["quarter"]).reset_index(drop=True)

    def _split_statements(self, df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """
        Retorna {'df_ind': DataFrame|None, 'df_con': DataFrame|None}.
        Regras:
        - Mantém linhas cujo grupo é exatamente IND ou CON.
        - Linhas de outros grupos são copiadas e atribuídas a IND e/ou CON conforme disponibilidade.
        - Se não existir IND nem CON, cria ambos a partir dos “outros”.
        """
        IND = "DFs Individuais"
        CON = "DFs Consolidadas"
        if "grupo" not in df.columns:
            raise ValueError("coluna 'grupo' ausente")

        df_ind0 = df[df["grupo"] == IND]
        df_con0 = df[df["grupo"] == CON]
        df_other = df[~df["grupo"].isin([IND, CON])].drop(columns=[], errors="ignore")

        has_ind = not df_ind0.empty
        has_con = not df_con0.empty
        has_other = not df_other.empty

        # Se não existir IND nem CON: cria os dois a partir de OTHER
        if not has_ind and not has_con:
            if not has_other:
                return {"df_ind": None, "df_con": None}
            df_ind = df_other.assign(grupo=IND)
            df_con = df_other.assign(grupo=CON)
            return {"df_ind": df_ind.reset_index(drop=True), "df_con": df_con.reset_index(drop=True)}

        # Construção do IND
        df_ind_parts = [df_ind0]
        if has_other:
            # “Outros” também pertencem ao IND quando IND existe
            df_ind_parts.append(df_other.assign(grupo=IND) if has_ind else pd.DataFrame())
        df_ind = pd.concat(df_ind_parts, ignore_index=True) if has_ind or has_other else None

        # Construção do CON
        df_con_parts = [df_con0]
        if has_other:
            # “Outros” também pertencem ao CON quando CON existe
            df_con_parts.append(df_other.assign(grupo=CON) if has_con else pd.DataFrame())
        df_con = pd.concat(df_con_parts, ignore_index=True) if has_con or (not has_ind and has_other) else (df_con0 if has_con else None)

        return {
            "df_ind": df_ind.reset_index(drop=True) if df_ind is not None and not df_ind.empty else None,
            "df_con": df_con.reset_index(drop=True) if df_con is not None and not df_con.empty else None,
            }

    def _load_quotes(self, ticker_codes: List, uow: Uow) -> pd.DataFrame:
        rows = self.repository_stock_quote.get_by_column_values(values=[("ticker", ticker_codes)], uow=uow)
        if not rows:
            from sqlalchemy.inspection import inspect
            model, _ = self.repository_stock_quote.get_model_class()
            columns = [c.key for c in inspect(model).mapper.column_attrs]
            return pd.DataFrame(columns=columns)

        quotes = pd.DataFrame(rows)
        quotes["date"] = pd.to_datetime(quotes["date"], errors="coerce")
        numeric_cols = ["open", "low", "high", "close", "adj_close", "volume"]
        for col in numeric_cols:
            quotes[col] = pd.to_numeric(quotes[col], errors="coerce")
        quotes.sort_values(["ticker", "date"], inplace=True)
        return quotes.dropna(subset=["date"]).reset_index(drop=True)

