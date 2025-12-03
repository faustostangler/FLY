import re
import time
from datetime import datetime, timedelta
from typing import Any, cast, List, Optional

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

import domain.utils.intel as intel
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import Uow, UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.services.cache_ratios_service import CacheRatiosService
from domain.dtos.cache_ratios_result_dto import CacheRatiosResultDTO
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from infrastructure.models.company_eligible_model import CompanyEligibleModel
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.ports.cache_ratios_port import CacheRatiosPort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.companies_eligible_port import CompaniesEligiblePort


class NormalizeUseCase:
    """Use case for synchronizing data between scraper and repository."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,

        repository_stock_quote: RepositoryStockQuotePort,
        repository_indicators: RepositoryIndicatorsPort,
        repository_statements_fetched: RepositoryStatementFetchedPort,
        cache_ratios: CacheRatiosPort,
        companies_eligible_port: CompaniesEligiblePort,

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
        self.repository_stock_quote = repository_stock_quote
        self.repository_indicators = repository_indicators
        self.repository_statements_fetched = repository_statements_fetched
        self.cache_ratios_service = CacheRatiosService(
                cache_port=cache_ratios,
                logical_name=self.config.fly_settings.app_name,
                version=self.config.fly_settings.version
                )
        self._ratios_code_hash = CacheRatiosService.build_code_hash([self._create_ratios, intel,])

        self.uow_factory = uow_factory
        self.worker_pool = worker_pool

        self.max_workers = max_workers or self.config.worker_pool.max_workers or 1
        self.companies_eligible_port = companies_eligible_port

    @property
    def ratios_code_hash(self) -> str:
        """Expose the code hash used for cache coordination."""

        return self._ratios_code_hash

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.run(companies=kwds.get("companies"))

    def run(self, companies:pd.DataFrame) -> SyncResultsDTO:
        """Run the full synchronization pipeline.

        Steps:
            1. Retrieve company data from the persistence layer.
            2. Transform results into normalized ``pandas`` data structures.
            3. Cache the calculated ratios for reuse across runs.

        Returns:
            SyncCompanyDataResultDTO: Summary of the synchronization process,
            including counts and network usage metrics.
        """
        metrics = 0
        cache_results: List[CacheRatiosResultDTO] = []
        start_time = time.perf_counter()

        if companies.empty:
            return SyncResultsDTO(items=[], metrics=0)
        total_companies = len(companies)

        try:
            with self.uow_factory() as bootstrap_uow:
                indicators = self._load_indicators(uow=bootstrap_uow)
                treated_indicators = {
                    indicator: self._treat_indicators(indicator_df)
                    for indicator, indicator_df in indicators.items()
                }

                def processor(task: WorkerTaskDTO) -> Optional[dict[str, Any]]:  # noqa: ANN401
                    company_dto = task.data["company_dto"]
                    len_s = 0
                    len_q = 0
                    cache_result: CacheRatiosResultDTO | None = None
                    metrics_value = 0

                    with self.uow_factory() as uow:

                        success = False
                        try:
                            quotes = self._load_quotes(ticker_codes=company_dto.ticker_codes, uow=uow)
                            statements = self._load_statements(company_name=company_dto.company_name, uow=uow)
                            len_s = len(statements.get("statements", []))
                            len_q = sum(len(v) for v in quotes.values())
                            data_snapshot = {
                                "indicators": treated_indicators,
                                "statements": statements,
                                "quotes": quotes,
                            }
                            # allowed_aggregate_methods = ['last', 'first', 'mean', 'median', 'max', 'min', 'sum', 'std', 'var']
                            company_data = self._treat_data(data_snapshot, aggregate_method='last')
                            df, cache_result = self.cache_ratios_service.get_or_compute(
                                company_name=company_dto.company_name,
                                quotes=company_data.get("quotes"),
                                statements=company_data.get("statements"),
                                indicators=company_data.get("indicators"),
                                compute_fn=lambda: self._create_ratios(company_data),
                                code_hash=self._ratios_code_hash,
                            )
                            metrics_value = cache_result.entry.size_bytes

                            success = True

                        except Exception as e:  # noqa: BLE001
                            self.logger.log(
                                f"NormalizeUseCase company {company_dto.company_name} failed: {e}",
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
                                # "Indicators": len(treated_indicators) or 0,
                                # "Statements": len_s,
                                # "Quotes": len_q,
                                "Cache": "hit" if cache_result and cache_result.hit else "cache" if cache_result else "skip",
                            }
                            ticker_str = " ".join(company_dto.ticker_codes).strip() if company_dto.ticker_codes else ""
                            self.logger.log(
                                f"{' '.join([ticker_str.strip(), company_dto.company_name]).strip()}",
                                level="info",
                                progress=progress,
                                extra=extra_info,
                            )

                            if success:
                                uow.commit()

                    if not cache_result:
                        return None

                    return {
                        "company_name": company_dto.company_name,
                        "cache_result": cache_result,
                        "metrics": metrics_value,
                    }

                def on_result(item: Optional[dict[str, Any]]) -> None:  # noqa: ANN401
                    nonlocal metrics
                    if not item:
                        return

                    cache_results.append(item["cache_result"])
                    metrics += int(item.get("metrics", 0))

                records = cast(list[dict[str, Any]], companies.to_dict(orient="records"))
                tasks = (
                    (index, {"company_dto": CompanyEligibleModel(**record).to_dto()},)
                    for index, record in enumerate(records)
                )

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
            self.logger.log(f"NormalizeUseCase failed: {exc}", level="error")
            raise

        results: SyncResultsDTO = SyncResultsDTO(
            items=cache_results,
            metrics=metrics,
        )

        return results

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

        if has_con:
            statements_df['df_consolidadas'] = _build_set(df_con0, has_other and has_con, df_other)
        if has_ind:
            statements_df['df_individuais'] = _build_set(df_ind0, has_other and has_ind, df_other)

        return statements_df

    def _load_quotes(self, ticker_codes: List, uow: Uow) -> dict[str, pd.DataFrame]:
        quotes_df = {}
        for ticker in ticker_codes:
            rows = self.repository_stock_quote.get_by_column_values(values=[("ticker", ticker)], uow=uow)
            if not rows:
                continue

            quotes = pd.DataFrame(rows)
            quotes["date"] = pd.to_datetime(quotes["date"], errors="coerce")
            numeric_cols = ["open", "low", "high", "close", "adj_close", "volume"]
            for col in numeric_cols:
                quotes[col] = pd.to_numeric(quotes[col], errors="coerce")
            quotes.sort_values(["ticker", "date"], inplace=True)


            m = re.search(r'\d+$', ticker)
            digit = m.group() if m else ""
            key = f"stock_{digit}" if digit else f"stock_{len(quotes_df)+1}"
            quotes_df[key] = quotes.dropna(subset=["date"]).reset_index(drop=True)

        return quotes_df

    def _treat_quotes(self, q: pd.DataFrame, c: pd.DataFrame|None = None) -> pd.DataFrame:

        if "date" in q.columns:
            q["date"] = pd.to_datetime(q["date"])
            q = q.sort_values("date").drop_duplicates(subset=["date"]).set_index("date")
        else:
            q.index = pd.to_datetime(q.index)
            q = q.sort_index().drop_duplicates()

        if c is not None and not c.empty:
            q = q.sort_index().reindex(c.index, method="ffill")
            if q.iloc[0].isna().any():
                q = q.bfill()

        return q

    def _treat_statements(self, s: pd.DataFrame, c: pd.DataFrame|None = None) -> pd.DataFrame:
        s["quarter"] = pd.to_datetime(s["quarter"])

        key_columns = ["company_name", "quarter", "account"]
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
            s = s.copy()
            s = s.reset_index()

            s["quarter"] = pd.to_datetime(s["quarter"])
            s = (
                s.rename(columns={"quarter": "date"})
                .set_index("date")
                .sort_index()
            )

            s = s.reindex(c.index, method="ffill")
            if s.iloc[0].isna().any():
                s = s.bfill()

            s = s.set_index(context_columns, append=True).sort_index()

        return s

    def _treat_indicators(self, i: pd.DataFrame, c: pd.DataFrame|None = None) -> pd.DataFrame:
        if c is None:
            i["date"] = pd.to_datetime(i["date"])
            i = i.sort_values("date").drop_duplicates(subset=["date"]).set_index("date")
        else:
            i = i.sort_index().reindex(c.index, method="ffill")
            if i.iloc[0].isna().any():
                i = i.bfill()

        return i

    def _get_stock_calendar(self, data:dict[str, dict[str, pd.DataFrame]], cutoff:datetime) -> pd.DatetimeIndex:
        stock_calendar = pd.DatetimeIndex([])
        data_quotes = data.get("quotes", {})
        if data_quotes:
            for k, dfq in data_quotes.items():
                if isinstance(dfq, pd.DataFrame) and "date" in dfq.columns and not dfq.empty:
                    stock_calendar = pd.to_datetime(dfq["date"], errors="coerce")
                    stock_calendar = pd.DatetimeIndex(stock_calendar).tz_localize(None)
                    stock_calendar = stock_calendar[~stock_calendar.isna()]
                    stock_calendar = stock_calendar[stock_calendar > cutoff]
                    break

        return stock_calendar

    def _create_daily_calendar(self, data: dict[str, dict[str, pd.DataFrame]], cutoff:datetime) -> pd.DatetimeIndex:
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
        end = max(date_max, pd.Timestamp.now()) - pd.Timedelta(days=1)
        daily_calendar = pd.date_range(start, end, freq='B')

        return daily_calendar

    def _create_calendar(self, data: dict[str, dict[str, pd.DataFrame]], cutoff:datetime, granularity:str="month", aggregate_method:str="last") -> pd.DataFrame:
        cutoff = cutoff or datetime(year=2010, month=12, day=31)
        allowed_granularities = [
            'D', 'day', 'B', 'business days',  # Diária (calendário ou business)
            'ME', 'month', 'MS', 'month start',  # Mensal (end ou start)
            'QE', 'quarter', 'QS', 'quarter start',  # Trimestral
            'YE', 'year', 'YS', 'year start'  # Anual
            ]
        if granularity not in allowed_granularities:
            raise ValueError(f"Invalid granularity: {granularity}. Must be one of {allowed_granularities}.")
        allowed_aggregate_methods = ['last', 'first', 'mean', 'median', 'max', 'min', 'sum', 'std', 'var']
        if aggregate_method not in allowed_aggregate_methods:
            raise ValueError(f"Invalid aggregate_method: {aggregate_method}. Must be one of {allowed_aggregate_methods}.")

        daily_calendar = self._get_stock_calendar(data, cutoff)
        if daily_calendar.empty:
            daily_calendar = self._create_daily_calendar(data, cutoff)
        daily_calendar_2 = self._create_daily_calendar(data, cutoff)

        daily_series = pd.Series(1, index=daily_calendar) # Valor 1 em cada trading day

        if granularity == 'D':
            df_anchor_calendar = daily_calendar
            df_anchor_calendar = pd.DataFrame({"trading_days": daily_series}, index=daily_calendar)
        else:
            df_anchor_calendar = daily_series.groupby(pd.Grouper(freq=granularity)).size().to_frame(name="trading_days")
        df_anchor_calendar.index.name = 'date'

        return df_anchor_calendar

    def _infer_granularity(self, idx:pd.Index) -> str:
        """
        Infere a granularidade de um índice DatetimeIndex.

        Args:
            idx: pd.Index, esperado como DatetimeIndex.
            data_type: Tipo de dado ('quotes', 'statements', 'indicators') para ajustar lógica.

        Returns:
            str: Granularidade inferida ('day', 'month', 'quarter', 'year') ou 'unknown' se falhar.
        """
        if not isinstance(idx, pd.DatetimeIndex):
            try:
                idx = pd.to_datetime(idx, errors='coerce')
                idx = idx[~idx.isna()]
                if len(idx) < 2:
                    return 'unknown'
            except Exception as e:
                return 'unknown'

        inferred_freq = pd.infer_freq(idx)
        freq_map = {
            'D': 'day', 'B': 'business days',  # Diária (calendário ou business)
            'ME': 'month', 'MS': 'month',  # Mensal (end ou start)
            'QE': 'quarter', 'QS': 'quarter',  # Trimestral
            'YE': 'year', 'YS': 'year'  # Anual
        }
        if inferred_freq in freq_map:
            return freq_map[inferred_freq]

        deltas = np.diff(idx.view("i8"))  # Diferenças em nanossegundos
        if len(deltas) == 0:
            return 'unknown'

        med = np.median(deltas)
        d1 = pd.Timedelta(days=1).value  # 1 dia em nanossegundos

        if med <= 7 * d1:
            return 'B'
        if med <= 45 * d1:
            return 'ME'
        if med <= 120 * d1:
            return 'QE'
        return 'YE'


    def _resample_series(
        self,
        df_data: pd.DataFrame,
        df_anchor_calendar: pd.DataFrame,
        aggregate_method: str,
    ) -> pd.DataFrame:
        """
        Alinha df_data ao df_anchor_calendar com upsampling_action ou downsampling.

        Args:
            df_data: DataFrame com índice DatetimeIndex.
            df_anchor_calendar: DataFrame com índice date e coluna trading_days.
            granularity_anchor: Granularidade do anchor ('D', 'B', 'ME', 'QE', 'YE').
            aggregate_method: Método de agregação padrão ('last', 'mean', etc.).
            data_type: Tipo de dado ('quotes', 'statements', 'indicators').

        Returns:
            pd.DataFrame: DataFrame alinhado ao df_anchor_calendar.
        """
        df_data.to_csv("df_data.csv", index=True)
        df_anchor_calendar.to_csv("df_anchor_calendar.csv", index=True)
        if df_data.empty:
            return df_data

        if not isinstance(df_data.index, pd.DatetimeIndex):
            df_data.index = pd.to_datetime(df_data.index, errors='coerce')
            df_data = df_data.dropna(subset=[df_data.index.name])

        granularity_order = {'B': 1, 'D': 2, 'MS': 3,'ME': 4, 'QS': 5,'QE': 6, 'YS': 7,'YE': 8} # granularidade: menor significa mais fino, mais diário e detalhado
        granularity_anchor = pd.infer_freq(df_anchor_calendar.index) or 'B'
        granularity_data = self._infer_granularity(df_data.index)
        sampling_anchor = granularity_order[granularity_anchor]  # Default to 'business day'
        sampling_data = granularity_order.get(granularity_data, 1)  # Default to 'business day'
        if sampling_data > sampling_anchor:
            sampling_action = "upsampling" # dados grossos: precisa preencher com valores intermediários
        elif sampling_data < sampling_anchor:
            sampling_action = "downsampling" # dados finos: precisa agregar com valores agrupados
        else:
            sampling_action = "same" # apenas reindexar

        if sampling_action == "upsampling":
            df_data = df_data.sort_index()
            df_data = df_data.reindex(df_data.index.union(df_anchor_calendar.index))
            df_data = df_data.ffill().bfill()
            df_data = df_data.reindex(df_anchor_calendar.index).sort_index()
        elif sampling_action == "downsampling":
            df_data = df_data.sort_index()

            daily_index = pd.date_range(df_data.index.min(), df_data.index.max(), freq='B')
            df_data = df_data.reindex(daily_index).ffill().bfill()
            grouper_freq = granularity_anchor
            agg_dict = {}
            for col in df_data.columns:
                if col in ['open']:
                    agg_dict[col] = 'first'
                elif col in ['high']:
                    agg_dict[col] = 'max'
                elif col in ['low']:
                    agg_dict[col] = 'min'
                elif col in ['close', 'adj_close']:
                    agg_dict[col] = 'last'
                elif col in ['volume']:
                    agg_dict[col] = 'sum'
                else:
                    agg_dict[col] = aggregate_method

            df_data = df_data.groupby(pd.Grouper(freq=grouper_freq)).agg(agg_dict)
            df_data = df_data.reindex(df_anchor_calendar.index)

        return df_data

    def _treat_data(self, data:dict[str, dict[str, pd.DataFrame]], aggregate_method:str="last") -> dict[str, dict[str, pd.DataFrame]]:
        cutoff:datetime = datetime(year=2010, month=12, day=31)
        g_map:dict[str, str] = {'day': 'D', 'month': 'ME', 'quarter': 'QE', 'year': 'Y'}
        granularity = g_map['day']
        calendar:pd.DataFrame = self._create_calendar(data, cutoff, granularity=granularity, aggregate_method=aggregate_method)

        data_treated = {}
        for k, d in data.items():
            k = "quotes"
            data_treated[k] = {}
            for stock_quote, df_stock_quote in data[k].items():
                df_stock_quote = df_stock_quote.set_index('date')
                resampled = self._resample_series(df_stock_quote, calendar, aggregate_method=aggregate_method)
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
        ''' Description'''
        source_df = c['statements']['statements'].copy()
        ratios_df = source_df.copy()

        quotes: dict[str, pd.DataFrame] = c.get("quotes", {}) or {}

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

            dfq = dfq.loc[:, [c for c in dfq.columns if c not in ignore_stock_keys_cols]].copy()
            if dfq.empty:
                continue

            dfq.columns = [f"{code}.{c} - {qkey}" for c in dfq.columns]
            frames.append(dfq)

        if frames:
            price_df = pd.concat(frames, axis=1)
            source_df = source_df.join(price_df, how='left')
            ratios_df = ratios_df.join(price_df, how="left")

        account_long_map = {c: c.split(" - ")[0] for c in source_df.columns if " - " in c}
        calculate_df = source_df.rename(columns=account_long_map).copy()

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

        if isinstance(ratios_df.index, pd.MultiIndex):
            ratios_df = ratios_df.reset_index(drop=False)  # transforma níveis do índice em colunas
            ratios_df = ratios_df.set_index("date").sort_index()

        return ratios_df.fillna(0)

