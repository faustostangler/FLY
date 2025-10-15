from typing import Any, List, Optional

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import re

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
        data:dict = {}
        metrics=0
        code_parameter = re.compile(r"^[A-Z]{4}\d{1,2}[A-Z]?$")
        start_time = time.perf_counter()
        with self.uow_factory() as uow:
            try:
                indicators = self._load_indicators(uow=uow)
                data['indicators'] = {}
                for indicator, df_indicator in indicators.items():
                    data["indicators"][indicator] = self._treat_indicators(df_indicator)

                companies = [company for (company,) in self.repository_company.iter_existing_by_columns("company_name", uow=uow)]
                if not companies:
                    self.logger.log("ERRO companies normalize", level="warning")
                    raise Exception

                for i, company_name in enumerate(companies):
                    len_s = 0
                    len_q = 0
                    # if company_name == "ALPARGATAS SA":
                    # if i > 30:
                    #     break
                    rows = self.repository_company.get_by_column_values(values=[("company_name", company_name)], uow=uow)
                    pre_ticker_codes:List = next((row.ticker_codes for row in rows if row.company_name == company_name),[],)
                    ticker_codes = [
                        code for code in pre_ticker_codes
                        if isinstance(code, str) and len(code) >= 5 and code_parameter.match(code)
                        ]
                    if ticker_codes:
                        data['statements'] = self._load_statements(company_name=company_name, uow=uow)
                        if data['statements']:
                            data['quotes'] = self._load_quotes(ticker_codes=ticker_codes, uow=uow)
                            if data['quotes']:
                                len_s = len(data['statements'])
                                len_q = len(data['quotes'])
                                company_data = self._treat_data(data)
                                df_ratios:pd.DataFrame = self._create_ratios(company_data)

                    progress={
                            "index": i,
                            "size": len(companies),
                            "start_time": start_time,  # noqa: F821 (assumed provided in context)
                        }
                    extra_info = {
                            # "Ticker Codes": ticker_codes,
                            "Indicators": len(data['indicators']) or 0,
                            "Statements": len_s,
                            "Quotes": len_q,
                        }

                    ticker_str = ' '.join(ticker_codes).strip() if ticker_codes else ''
                    self.logger.log(f"{ticker_str} {company_name}", level="info", progress=progress, extra=extra_info)

            except Exception as e:
                self.logger.log(f"NormalizeUseCase failed: {e}", level="error")
                raise

        results:SyncResultsDTO = SyncResultsDTO(
            items=df_ratios,
            metrics=metrics,
        )

        return results

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
                .reset_index()
            )
            matrices[str(code)] = pivot

        return matrices

    def _load_statements(self, company_name:str, uow: Uow) -> dict[str, pd.DataFrame]:
        statements_df = {}
        rows = self.repository_statements_fetched.get_by_column_values(values=[("company_name", company_name)], uow=uow)
        if not rows:
            return statements_df

        def _build_set(df: pd.DataFrame, use_other: bool, df_other: pd.DataFrame) -> pd.DataFrame:
            if df is None or df.empty:
                return pd.DataFrame()
            parts = [df]
            if use_other and df_other is not None and not df_other.empty:
                parts.append(df_other)
            out = pd.concat(parts, ignore_index=True)
            return out.sort_values(["quarter", "account"], kind="mergesort").reset_index(drop=True)

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

        if has_con:
            statements_df['statements'] = _build_set(df_ind0, has_other and has_ind, df_other)
        else:
            statements_df['statements'] = _build_set(df_ind0, has_other and has_ind, df_other)

        return statements_df

    def _load_quotes(self, ticker_codes: List, uow: Uow) -> dict[str, pd.DataFrame]:
        quotes_df = {}
        for ticker in ticker_codes:
            rows = self.repository_stock_quote.get_by_column_values(values=[("ticker", ticker)], uow=uow)
            if not rows:
                return quotes_df

            quotes = pd.DataFrame(rows)
            quotes["date"] = pd.to_datetime(quotes["date"], errors="coerce")
            numeric_cols = ["open", "low", "high", "close", "adj_close", "volume"]
            for col in numeric_cols:
                quotes[col] = pd.to_numeric(quotes[col], errors="coerce")
            quotes.sort_values(["ticker", "date"], inplace=True)

            digit = re.search(r'\d+$', ticker).group() if re.search(r'\d+$', ticker) else None 
            quotes_df[f"stock_{digit}"] = quotes.dropna(subset=["date"]).reset_index(drop=True)

        return quotes_df

    def _treat_quotes(self, q: pd.DataFrame, c: pd.DataFrame|None = None) -> pd.DataFrame:
        # if c.empty:
        #     return pd.DataFrame()

        q["date"] = pd.to_datetime(q["date"])
        q = q.sort_values("date").drop_duplicates(subset=["date"]).set_index("date")

        if c is not None and not c.empty:
            q = q.sort_index().reindex(c.index, method="ffill")
            if q.iloc[0].isna().any():
                q = q.bfill()

        return q

    def _treat_statements(self, s: pd.DataFrame, c: pd.DataFrame|None = None) -> pd.DataFrame:
        # if c.empty:
        #     return pd.DataFrame()

        key_columns = ["company_name", "quarter", "grupo", "quadro", "account"]
        s["account_description"] = s["account"].str.cat(s["description"], sep=" - ")
        s["quarter"] = pd.to_datetime(s["quarter"])
        s = s.sort_values(key_columns)
        s = s.drop_duplicates(subset=key_columns, keep="last")
        statements_wide = s.pivot_table(index="quarter",
                                columns="account_description",  # use "description" se preferir nomes ou "account" se preferir contas
                                values="value",
                                aggfunc="last").sort_index()
        statements_wide.columns.name = None

        if c is not None and not c.empty:
            s = statements_wide.sort_index().reindex(c.index, method="ffill")
            if s.iloc[0].isna().any():
                s = s.bfill()

        return s

    def _treat_indicators(self, i: pd.DataFrame, c: pd.DataFrame|None = None) -> pd.DataFrame:
        # if c is None or c.empty: 
        #     return pd.DataFrame()
        if c is None:
            i["date"] = pd.to_datetime(i["date"])
            i = i.sort_values("date").drop_duplicates(subset=["date"]).set_index("date")
        else:
            i = i.sort_index().reindex(c.index, method="ffill")
            if i.iloc[0].isna().any():
                i = i.bfill()

        return i

    def _treat_data(self, data:dict[str, dict[str, pd.DataFrame]]) -> dict[str, dict[str, pd.DataFrame]]:
        cutoff = datetime(year=2010, month=12, day=31)
        if cutoff:
            key = next(iter(data["quotes"].keys()), None)
            calendar = data["quotes"][key].set_index('date').iloc[:, :0]
            calendar = calendar[calendar.index > cutoff]

        data_treated = {}

        for k, d in data.items():
            k = "quotes"
            data_treated[k] = {}
            for stock_quote, df_stock_quote in data[k].items():
                data_treated[k][stock_quote] = self._treat_quotes(df_stock_quote, calendar)

            k = "statements"
            data_treated[k] = {}
            if data[k]:
                for statement, df_statement in data[k].items():
                    data_treated[k][statement] = self._treat_statements(df_statement, calendar)
            else:
                data_treated[k] = []

            k = "indicators"
            data_treated[k] = {}
            if data[k]:
                for indicator, df_indicator in data[k].items():
                    data_treated[k][indicator] = self._treat_indicators(df_indicator, calendar)
            else:
                data_treated[k] = []

        return data_treated

    def _create_ratios(self, company_data:dict[str, dict[str, pd.DataFrame]]) -> pd.DataFrame:
        result = pd.DataFrame()

        data = {}

        if 'con' in company_data['statements']:
            data['statements'] = company_data['statements']['con']
        elif 'ind' in company_data['statements']:
            data['statements'] = company_data['statements']['ind']

        for ticker, df in company_data['quotes'].items():
            digit = re.search(r'\d+$', ticker).group() if re.search(r'\d+$', ticker) else None 
            data[f"stock_{digit}"] = df

        data['indicators'] = company_data['indicators']



        return result
