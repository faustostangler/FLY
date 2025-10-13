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
                companies = [company for (company,) in self.repository_company.iter_existing_by_columns("company_name", uow=uow)]
                if not companies:
                    return SyncResultsDTO(items=[], metrics=0)

                indicators_df = self._load_indicators(uow=uow)

                for company_name in companies:
                    if company_name == "ALPARGATAS SA":
                        rows = self.repository_company.get_by_column_values(values=[("company_name", company_name)], uow=uow)
                        ticker_codes:List = next((row.ticker_codes for row in rows if row.company_name == company_name),[],)
                        statements_df = self._load_statements(company_name=company_name, uow=uow)

                        quotes_df = self._load_quotes(ticker_codes=ticker_codes, uow=uow)

            except Exception as e:
                self.logger.log(f"NormalizeUseCase failed: {e}", level="error")
                raise

    def _load_indicators(self, uow: Uow) -> dict[str, pd.DataFrame]:
        matrices: dict[str, pd.DataFrame] = {}

        rows = self.repository_indicators.get_all(uow=uow)
        if not rows:
            return matrices

        indicators = pd.DataFrame(rows)
        indicators["date"] = pd.to_datetime(indicators["date"], errors="coerce")
        indicators["value"] = pd.to_numeric(indicators["value"], errors="coerce")
        indicators.sort_values(["code", "name", "date"], inplace=True)
        indicators = indicators.dropna(subset=["date"]).reset_index(drop=True)

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

        return matrices

    def _load_statements(self, company_name:str, uow: Uow) -> dict[str, pd.DataFrame]:
        statements_df = {}
        rows = self.repository_statements_fetched.get_by_column_values(values=[("company_name", company_name)], uow=uow)
        if not rows:
            return statements_df

        statements = pd.DataFrame(rows)
        statements["quarter"] = pd.to_datetime(statements["quarter"], errors="coerce")
        statements["value"] = pd.to_numeric(statements["value"], errors="coerce")
        statements["version_numeric"] = pd.to_numeric(statements["version"], errors="coerce").fillna(-1)
        statements.sort_values(["company_name", "quarter", "version_numeric"], inplace=True)
        df = statements.dropna(subset=["quarter"]).reset_index(drop=True)

        # keep latest version only, just in case
        mask = df["version_numeric"] == df.groupby("quarter")["version_numeric"].transform("max")
        df = df[mask].reset_index(drop=True)

        if "grupo" not in df.columns:
            raise ValueError("coluna 'grupo' ausente")

        df_ind0 = df[df["grupo"] == "DFs Individuais"]
        df_con0 = df[df["grupo"] == "DFs Consolidadas"]
        df_other = df[~df["grupo"].isin(["DFs Individuais", "DFs Consolidadas"])].drop(columns=[], errors="ignore")

        has_ind = not df_ind0.empty
        has_con = not df_con0.empty
        has_other = not df_other.empty

        def _build_set(df: pd.DataFrame, use_other: bool, df_other: pd.DataFrame) -> pd.DataFrame:
            if df is None or df.empty:
                return pd.DataFrame()
            parts = [df]
            if use_other and df_other is not None and not df_other.empty:
                parts.append(df_other)
            out = pd.concat(parts, ignore_index=True)
            return out.sort_values(["quarter", "account"], kind="mergesort").reset_index(drop=True)

        statements_df['ind'] = _build_set(df_ind0, has_other and has_ind, df_other)
        statements_df['con'] = _build_set(df_con0, has_other and has_con, df_other)

        return statements_df

    def _load_quotes(self, ticker_codes: List, uow: Uow) -> dict[str, pd.DataFrame]:
        quotes_df = {}
        for ticker in ticker_codes:
            rows = self.repository_stock_quote.get_by_column_values(values=[("ticker", ticker)], uow=uow)
            if not rows:
                from sqlalchemy.inspection import inspect
                model, _ = self.repository_stock_quote.get_model_class()
                columns = [c.key for c in inspect(model).mapper.column_attrs]
                quotes_df[ticker] = pd.DataFrame(columns=columns)

            quotes = pd.DataFrame(rows)
            quotes["date"] = pd.to_datetime(quotes["date"], errors="coerce")
            numeric_cols = ["open", "low", "high", "close", "adj_close", "volume"]
            for col in numeric_cols:
                quotes[col] = pd.to_numeric(quotes[col], errors="coerce")
            quotes.sort_values(["ticker", "date"], inplace=True)
            quotes_df[ticker] = quotes.dropna(subset=["date"]).reset_index(drop=True)
        return quotes_df

