import hashlib
import re
import time
from datetime import datetime, timedelta
from typing import Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

import domain.utils.intel as intel
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.ports.uow_port import Uow, UowFactoryPort
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.dtos.company_data_dto import CompanyDataDTO
from domain.dtos.statement_ratio_dto import StatementRatioDTO
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_statements_ratio_port import RepositoryStatementRatioPort
from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from infrastructure.utils.list_flatenner import ListFlattener
from infrastructure.utils.save_strategy import SaveStrategy

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
        repository_statements_ratio: RepositoryStatementRatioPort,
        repository_statements_fetched: RepositoryStatementFetchedPort,

        uow_factory: UowFactoryPort,
        worker_pool: WorkerPoolPort,

        max_workers: int | None = None,
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
        self.repository_statements_ratio = repository_statements_ratio
        self.repository_statements_fetched = repository_statements_fetched

        self.uow_factory = uow_factory
        self.worker_pool = worker_pool

        self.max_workers = max_workers or self.config.worker_pool.max_workers or 1

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
        metrics = 0
        all_ratios: List[StatementRatioDTO] = []
        code_parameter = re.compile(r"^[A-Z]{4}\d{1,2}[A-Z]?$")
        start_time = time.perf_counter()

        strategy: SaveStrategy[StatementRatioDTO] = SaveStrategy.from_config(
            self._save_ratios_batch,
            threshold=self.config.repository.persistence_threshold,
            config=self.config,
            auto_flush=False,
            uow_factory=self.uow_factory,
        )

        try:
            with self.uow_factory() as bootstrap_uow:
                indicators = self._load_indicators(uow=bootstrap_uow)
                treated_indicators = {
                    indicator: self._treat_indicators(indicator_df)
                    for indicator, indicator_df in indicators.items()
                }

                companies = [
                    company
                    for (company,) in self.repository_company.iter_existing_by_columns(
                        "company_name", uow=bootstrap_uow
                    )
                ]

                if not companies:
                    self.logger.log("ERRO companies normalize", level="warning")
                    raise Exception("Nenhuma companhia encontrada para normalização")

        except Exception as exc:  # noqa: BLE001
            self.logger.log(f"NormalizeUseCase failed: {exc}", level="error")
            raise

        total_companies = len(companies)

        def processor(task: WorkerTaskDTO) -> Optional[dict[str, Any]]:  # noqa: ANN401
            company_name = task.data["company_name"]
            len_s = 0
            len_q = 0
            ratios_dtos: List[StatementRatioDTO] = []
            ticker_codes: List[str] = []

            with self.uow_factory() as uow:
                success = False
                try:
                    company_rows = self.repository_company.get_by_column_values(
                        values=[("company_name", company_name)],
                        uow=uow,
                    )
                    company_row: Optional[CompanyDataDTO] = next(
                        (row for row in company_rows if row.company_name == company_name),
                        None,
                    )

                    if company_row:
                        ticker_codes = [
                            code
                            for code in (company_row.ticker_codes or [])
                            if isinstance(code, str)
                            and len(code) >= 5
                            and code_parameter.match(code)
                        ]

                    if ticker_codes and len(ticker_codes[0]) > 4:
                        quotes = self._load_quotes(ticker_codes=ticker_codes, uow=uow)
                        if quotes:
                            statements = self._load_statements(company_name=company_name, uow=uow)
                            if statements:
                                # check if need to update
                                with self.uow_factory() as uow:
                                    if not self._should_process(company_name, uow=uow):
                                        return  # sai antes de _treat_data

                                len_s = len(statements.get("statements", []))
                                len_q = sum(len(v) for v in quotes.values())
                                data_snapshot = {
                                    "indicators": treated_indicators,
                                    "statements": statements,
                                    "quotes": quotes,
                                }

                                company_data = self._treat_data(data_snapshot)
                                df_ratios = self._create_ratios(company_data)
                                ratios_dtos = self._build_ratio_dtos(
                                    df_ratios=df_ratios,
                                    company=company_row,
                                    ticker_codes=ticker_codes,
                                )

                    success = True

                except Exception as error:  # noqa: BLE001
                    self.logger.log(
                        f"NormalizeUseCase company {company_name} failed: {error}",
                        level="error",
                    )
                    raise
                finally:
                    progress = {
                        "index": task.index,
                        "size": total_companies,
                        "start_time": start_time,
                    }
                    extra_info = {
                        "Indicators": len(treated_indicators) or 0,
                        "Statements": len_s,
                        "Quotes": len_q,
                    }
                    ticker_str = " ".join(ticker_codes).strip() if ticker_codes else ""
                    self.logger.log(
                        f"{' '.join([ticker_str.strip(), company_name]).strip()}",
                        level="info",
                        progress=progress,
                        extra=extra_info,
                    )

                    if success:
                        uow.commit()

            if not ratios_dtos:
                return None

            return {
                "company_name": company_name,
                "ratios": ratios_dtos,
            }

        local_buffer: list[Any] = []
        def handle_batch(item: Optional[dict[str, Any]]) -> None:  # noqa: ANN401
            if not item:
                return

            local_buffer.append(item.get("ratios", []))  # mantém bloco de listas

            # Flush imediatamente se atingir o limite e auto_flush estiver ativo
            if len(local_buffer) >= strategy.threshold:
                # strategy.handle(item.get("ratios", []))  # enfileira o bloco de 3 dtos
                strategy.handle_many(local_buffer)
                strategy.flush()
                local_buffer.clear()
            # with self.uow_factory() as uow:
            #     strategy.handle(item.get("ratios", []))
            #     # strategy.handle_many(item.get("ratios", []))
            #     # strategy.flush(uow=uow)
            #     # uow.commit()
            #     pass

        def on_result(item: Optional[dict[str, Any]]) -> None:  # noqa: ANN401
            nonlocal metrics
            handle_batch(item)
            if not item:
                return

            ratios = item.get("ratios", [])
            all_ratios.extend(ratios)
            metrics += len(ratios)

        tasks = (
            (index, {"company_name": company_name})
            for index, company_name in enumerate(companies)
        )

        try:
            self.worker_pool(
                logger=self.logger,
                tasks=tasks,
                processor=processor,
                on_result=on_result,
                post_callback=None,
                max_workers=self.max_workers,
                total_size=total_companies,
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.log(
                f"NormalizeUseCase processing failed: {exc}",
                level="error",
            )
            raise
        finally:
            strategy.finalize()

        results: SyncResultsDTO = SyncResultsDTO(
            items=all_ratios,
            metrics=metrics,
        )

        return results

    def _should_process(self, company: str, *, uow: Uow) -> bool:
        fetched_head = self.repository_statements_fetched.get_head(company, uow=uow)
        if not fetched_head:
            return False

        ratio_head = self.repository_statements_ratio.get_head(company, uow=uow)
        if not ratio_head:
            return True

        return fetched_head > ratio_head

    def _save_ratios_batch(
        self,
        items: List[StatementRatioDTO],
        *,
        uow: Uow,
    ) -> None:
        if not items:
            return

        self.repository_statements_ratio.save_all(items, uow=uow)

    def _load_indicators(self, uow: Uow) -> dict[str, pd.DataFrame]:
        indicators: dict[str, pd.DataFrame] = {}

        rows = self.repository_indicators.get_all(uow=uow)
        if not rows:
            return indicators

        indicators_df = pd.DataFrame(rows)
        indicators_df["date"] = pd.to_datetime(indicators_df["date"], errors="coerce")
        indicators_df["value"] = pd.to_numeric(indicators_df["value"], errors="coerce")
        indicators_df.sort_values(["code", "name", "date"], inplace=True)
        indicators_df = indicators_df.dropna(subset=["date"]).reset_index(drop=True)

        for (source, code), group in indicators_df.groupby(["source", "code"]):
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
            indicators[str(code)] = pivot

        return indicators

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
            statements_df['statements'] = _build_set(df_con0, has_other and has_con, df_other)
        else:
            statements_df['statements'] = _build_set(df_ind0, has_other and has_ind, df_other)

        return statements_df

    def _load_quotes(self, ticker_codes: List, uow: Uow) -> dict[str, pd.DataFrame]:
        quotes_df = {}
        for ticker in ticker_codes:
            rows = self.repository_stock_quote.get_by_column_values(values=[("ticker", ticker)], uow=uow)
            if not rows:
                # return quotes_df
                continue

            quotes = pd.DataFrame(rows)
            quotes["date"] = pd.to_datetime(quotes["date"], errors="coerce")
            numeric_cols = ["open", "low", "high", "close", "adj_close", "volume"]
            for col in numeric_cols:
                quotes[col] = pd.to_numeric(quotes[col], errors="coerce")
            quotes.sort_values(["ticker", "date"], inplace=True)

            # digit = re.search(r'\d+$', ticker).group() if re.search(r'\d+$', ticker) else None 
            # quotes_df[f"stock_{digit}"] = quotes.dropna(subset=["date"]).reset_index(drop=True)

            m = re.search(r'\d+$', ticker)
            digit = m.group() if m else ""
            key = f"stock_{digit}" if digit else f"stock_{len(quotes_df)+1}"
            quotes_df[key] = quotes.dropna(subset=["date"]).reset_index(drop=True)

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
        s["quarter"] = pd.to_datetime(s["quarter"])

        key_columns = ["company_name", "quarter", "account"]
        # sep = " - "
        s["account_description"] = s["account"] + " - " + s["description"] + " - " + s["grupo"] + " - " + s["quadro"]

        context_columns = ["nsd", "company_name", "version"]
        meta = (
            s[["quarter"] + context_columns]
            .drop_duplicates(subset=["quarter"], keep="last")
            .set_index("quarter")
        )

        s = s.sort_values(key_columns)
        s = s.drop_duplicates(subset=key_columns, keep="last")
        s = s.pivot_table(index=["quarter"],
                                columns="account_description",  # use "description" se preferir nomes ou "account" se preferir contas
                                values="value",
                                aggfunc="last").sort_index()
        s.columns.name = None

        s = meta.join(s, how="right")

        if c is not None:
            # reset_multiindex
            s = s.copy()
            # s.index = s.index.set_names(["quarter", "nsd", "company_name", "version"])
            s = s.reset_index()

            # create date index
            s["quarter"] = pd.to_datetime(s["quarter"])
            s = (
                s.rename(columns={"quarter": "date"})
                .set_index("date")
                .sort_index()
            )

            # reindex ffill bfill
            s = s.reindex(c.index, method="ffill")
            if s.iloc[0].isna().any():
                s = s.bfill()

            # recreate multiindex
            s = s.set_index(context_columns, append=True).sort_index()

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

    def _create_daily_calendar(self, data: dict[str, dict[str, pd.DataFrame]], cutoff:datetime) -> pd.DataFrame:
        date_min = cutoff
        date_max = pd.Timestamp.now()
        data_quotes = data.get("quotes", {})
        data_statements = data.get("statements", {})
        data_indicators = data.get("indicators", {})

        if data_quotes:
            mins = []
            maxs = []
            for k, dfq in data_quotes.items():
                if isinstance(dfq, pd.DataFrame) and "date" in dfq.columns and not dfq.empty:
                    dts = pd.to_datetime(dfq["date"], errors="coerce")
                    dts = pd.DatetimeIndex(dts).tz_localize(None)
                    dts = dts[~dts.isna()]
                    if len(dts):
                        mins.append(dts.min())
                        maxs.append(dts.max())
            if mins:
                date_min = min(mins)
            if maxs:
                date_max = max(maxs)

        if date_min == cutoff and data_statements:
            statements = data.get("statements", {}).get("statements")
            if statements is not None and not statements.empty and "quarter" in statements.columns:
                dates = pd.to_datetime(statements["quarter"].unique())
                date_min = dates.min().tz_localize(None)
                date_max = dates.max().tz_localize(None)

        if date_min == cutoff and data_indicators:
            mins = []
            maxs = []
            for k, dfi in data_indicators.items():
                if isinstance(dfi, pd.DataFrame) and not dfi.empty:
                    dts = pd.to_datetime(dfi.index, errors="coerce").tz_localize(None)
                    dts = dts[~dts.isna()]
                    if len(dts):
                        mins.append(dts.min())
                        maxs.append(dts.max())
            if mins:
                date_min = min(mins)
            if maxs:
                date_max = max(maxs)

        start = max(date_min, pd.Timestamp(cutoff)) + pd.Timedelta(days=1)
        end = min(date_max, pd.Timestamp.now()) - pd.Timedelta(days=1)
        daily_calendar = pd.DataFrame(index=pd.date_range(start, end, freq='D'))

        return daily_calendar

    def _create_calendar(self, data: dict[str, dict[str, pd.DataFrame]], cutoff:datetime, granularity:str="month", aggregate_method:str="last") -> pd.DataFrame:
        cutoff = cutoff or datetime(year=2010, month=12, day=31)
        allowed_granularities = ['day', 'month', 'quarter', 'year']
        if granularity not in allowed_granularities:
            raise ValueError(f"Invalid granularity: {granularity}. Must be one of {allowed_granularities}.")
        allowed_aggregate_methods = ['last', 'first', 'mean', 'median', 'max', 'min', 'sum', 'std', 'var']
        if aggregate_method not in allowed_aggregate_methods:
            raise ValueError(f"Invalid agg_method: {aggregate_method}. Must be one of {allowed_aggregate_methods}.")
        calendar_frequency_map:dict[str, str] = {'day': 'D', 'month': 'M', 'quarter': 'Q', 'year': 'Y'}
        calendar = pd.DataFrame()

        daily_calendar = self._create_daily_calendar(data, cutoff)


        return calendar

    def _treat_data(self, data:dict[str, dict[str, pd.DataFrame]]) -> dict[str, dict[str, pd.DataFrame]]:
        cutoff = datetime(year=2010, month=12, day=31)
        calendar = self._create_calendar(data, cutoff, granularity="month", aggregate_method="last")

        quotes_map: dict[str, pd.DataFrame] = data.get("quotes", {}) or {}
        if quotes_map:
            # pega a primeira série válida com coluna 'date'
            for k, dfq in quotes_map.items():
                if isinstance(dfq, pd.DataFrame) and "date" in dfq.columns and not dfq.empty:
                    tmp = dfq.set_index("date").iloc[:, :0]
                    # tmp.index = pd.to_datetime(tmp.index, errors="coerce")
                    tmp.index = pd.to_datetime(tmp.index, errors="coerce").tz_localize(None)
                    mask = tmp.index.to_series().gt(cutoff)  # Series[bool], alinhada ao índice
                    calendar = tmp.loc[mask]
                    break  # encontrado o primeiro válido
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

    def _create_ratios(self, c: dict[str, dict[str, pd.DataFrame]]) -> pd.DataFrame:
        source_df = c['statements']['statements'].copy()
        ratios_df = source_df.copy()

        # preços por classe (fechamento), já reindexados pelo calendário em _treat_quotes
        quotes: dict[str, pd.DataFrame] = c.get("quotes", {}) or {}

        # coleta e ordena chaves stock_* independentemente de quantas existam
        stock_keys = [k for k in quotes.keys() if str(k).startswith('stock_')]
        stock_keys.sort(key=lambda x: int(str(x).split('_', 1)[1]) if '_' in str(x) else float('inf'))

        ignore_stock_keys_cols = ['id', 'date', 'company_name', 'ticker']
        frames = []

        for i, qkey in enumerate(stock_keys):
            try:
                suffix = qkey.split("_", 1)[1]           # '3', '4', ...
                code = f"99.{suffix}"
            except Exception:
                code = f"99.{i+3}"

            dfq = quotes.get(qkey)
            if dfq is None or dfq.empty:
                continue

            # filtra colunas relevantes
            dfq = dfq.loc[:, [c for c in dfq.columns if c not in ignore_stock_keys_cols]].copy()
            if dfq.empty:
                continue

            # renomeia todas as colunas em bloco
            dfq.columns = [f"{code}.{c} - {qkey}" for c in dfq.columns]
            frames.append(dfq)

        if frames:
            price_df = pd.concat(frames, axis=1)
            source_df = source_df.join(price_df, how='left')
            ratios_df = ratios_df.join(price_df, how="left")

        # mapeia uma vez e congela calculate_df base
        # account_long_map_old = {c: c.split(" - ")[0] for c in source_df.columns
        #             if " - " in c and not c.startswith("99.")}
        account_long_map = {c: c.split(" - ")[0] for c in source_df.columns if " - " in c}
        calculate_df = source_df.rename(columns=account_long_map).copy()

        # percorre TODAS as listas mantendo o mesmo calculate_df
        indicator_names = [
            name
            for name in dir(intel)
            if name.startswith('indicators_')
            and isinstance(getattr(intel, name), list)
            ]
        indicator_names.sort()

        for name in indicator_names:
            ratios_df = ratios_df.copy()
            calculate_df = calculate_df.copy()
            indicators_list = getattr(intel, name)
            for indicator in indicators_list:
                account_name = indicator["account"]
                description  = indicator["description"]
                formula_obj  = indicator["formula"]
                col_out = f"{account_name} - {description}"
                try:
                    series_value = formula_obj(calculate_df)
                    ratios_df[col_out] = series_value
                    calculate_df[account_name] = series_value   # persiste para loops
                except KeyError:
                    ratios_df[col_out] = np.nan
                    calculate_df[account_name] = np.nan   # persiste para loops
            
        return ratios_df.fillna(0)

    def _build_ratio_dtos(
        self,
        *,
        df_ratios: pd.DataFrame,
        company: Optional[CompanyDataDTO],
        ticker_codes: List[str],
    ) -> List[StatementRatioDTO]:
        if company is None or df_ratios.empty:
            return []
        tidy = df_ratios.reset_index()
        tidy["date"] = pd.to_datetime(tidy["date"], errors="coerce")

        tidy = tidy.dropna(subset=["date"])
        tidy['nsd'] = tidy['nsd'].astype(str)
        tidy['company_name'] = tidy['company_name'].astype(str)
        tidy['version'] = tidy['version'].astype(str)

        context_columns = ["nsd", "company_name", "version"] # quarter, account e value vão ser pivotados
        melted = tidy.melt(id_vars=["date"] + context_columns, var_name="account_description", value_name="value")
        if melted.empty:
            return []

        sep = " - "
        cols = ["account", "description", "grupo", "quadro"]
        parts = melted["account_description"].str.split(sep, n=3, expand=True)
        parts.columns = cols[:parts.shape[1]]
        for col in parts.columns:
            parts[col] = parts[col].str.strip()
        melted = melted.drop(columns=["account_description"]).join(parts)
        for col in cols:
            if col not in melted.columns:
                melted[col] = pd.NA
        melted[cols] = melted[cols].astype("string")
        melted = melted[[
            "company_name", "nsd", "date", "grupo", "quadro", "account", "description", "value", "version",
        ]]
        melted["grupo"] = melted["grupo"].replace("", pd.NA)
        melted["quadro"] = melted["quadro"].replace("", pd.NA)
        melted["grupo"] = melted["grupo"].fillna("Indicadores")
        suffix = melted["account"].fillna("").str[:2]
        melted["quadro"] = melted["quadro"].fillna("Indicador " + suffix)
        melted["value"] = pd.to_numeric(melted["value"], errors="coerce").fillna(0.0)
        melted = melted.sort_values(["company_name", "nsd", "date", "account"]).reset_index(drop=True)
        # melted.to_csv("melted.csv")

        ticker = ticker_codes[0] if ticker_codes else ""

        chunk_size = 100000
        start_time = time.perf_counter()
        dtos: list[StatementRatioDTO] = []
        for start in range(0, len(melted), chunk_size):
            chunk = melted.iloc[start:start + chunk_size]
            for company_name, nsd, d, grupo, quadro, account, description, value, version in chunk.itertuples(index=False, name=None):
                dto = StatementRatioDTO(
                    nsd=nsd,
                    company_name=company_name,
                    ticker=ticker,
                    date=d,
                    grupo=grupo,
                    quadro=quadro,
                    account=account,
                    description=description,
                    value=float(value) if value else 0.00,
                    version=version,
                )
                dtos.append(dto)
            progress={
                "index": start + len(chunk) - 1,
                "size": len(melted),
                "start_time": start_time,  # noqa: F821 (assumed provided in context)
            }
            extra_info = {
                "Info": "",
            }

            self.logger.log(f"{ticker}", level="info", progress=progress, extra=extra_info)
            pass

        return dtos

    # def _calculate_ratios(self, ratios_df: pd.DataFrame, source_df: pd.DataFrame, indicators_list: list) -> pd.DataFrame:
    #     # 1 Mapeamento
    #     account_map_long = {}
    #     account_map_short = {}
    #     for col in source_df.columns:
    #         try:
    #             account_code = col.split(' - ')[0]
    #             account_map_long[col] = account_code
    #             account_map_short[account_code] = col
    #         finally:
    #             pass

    #     # 2 temp rename
    #     calculate_df = source_df.rename(columns=account_map_long).copy()

    #     # 3 Indicators Formulas
    #     for indicator in indicators_list:
    #         account_name = indicator["account"]
    #         description = indicator["description"]
    #         formula_object = indicator["formula"]

    #         new_col_name = f"{account_name} - {description}"
    #         try:
    #             print(account_name)
    #             if account_name == '22.04':
    #                 pass
    #             series_value = formula_object(calculate_df)
    #             ratios_df[new_col_name] = series_value
    #             calculate_df[account_name] = series_value
    #         except KeyError as e:
    #             # self.logger.log(f"{new_col_name}. {e}.", level="error")
    #             ratios_df[new_col_name] = np.nan

    #     return ratios_df.copy()
