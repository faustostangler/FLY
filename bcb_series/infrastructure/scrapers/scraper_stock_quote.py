# infrastructure/adapters/scraper_stock_quote.py
from __future__ import annotations

import calendar
import time
from datetime import date, datetime
from typing import Iterable, List, Optional, Tuple, cast

import pandas as pd
import requests
import yfinance as yf  # dependência de infraestrutura

from application.ports.config_port import ConfigPort
from application.ports.http_client_port import AffinityHttpClientPort
from application.ports.logger_port import LoggerPort
from application.ports.metrics_collector_port import MetricsCollectorPort
from application.ports.uow_port import Uow, UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.scraper_base_port import ExistingItem, SaveCallback
from domain.ports.scraper_stock_quote_port import ScraperStockQuotePort
from infrastructure.utils.byte_formatter import ByteFormatter
from infrastructure.utils.save_strategy import SaveStrategy

StockQuoteExistingItem = Tuple[str, str, datetime | None, datetime]


class StockQuoteScraper(ScraperStockQuotePort):
    """Scraper de cotações com delta por ticker e saída em DTO."""

    def __init__(
        self,
        *,
        config: ConfigPort,
        logger: LoggerPort,
        repository_stock_quote: RepositoryStockQuotePort,
        metrics_collector: MetricsCollectorPort,
        worker_pool: WorkerPoolPort,
        http_client: AffinityHttpClientPort,
        uow_factory: UowFactoryPort,
    ) -> None:
        self.config = config
        self.logger = logger
        self.repository_stock_quote = repository_stock_quote

        self.worker_pool_executor = worker_pool
        self._metrics_collector = metrics_collector
        self.uow_factory = uow_factory
        self.http_client = http_client

        self.byte_formatter = ByteFormatter()

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        existing_codes: Optional[Iterable[ExistingItem]] = None,
        save_callback: Optional[SaveCallback[StockQuoteDTO]] = None,
        **kwargs,
    ) -> List[StockQuoteDTO]:
        """Stream de DTOs de `start..end` e persistência opcional em lotes."""

        raw_existing = list(existing_codes or [])
        normalized_existing: list[StockQuoteExistingItem] = []
        for entry in raw_existing:
            if isinstance(entry, tuple) and len(entry) == 4:
                ticker, company_name, start_date, end_date = entry
                if not isinstance(ticker, str) or not isinstance(company_name, str):
                    continue
                if start_date is not None and not isinstance(start_date, datetime):
                    continue
                if not isinstance(end_date, datetime):
                    continue
                normalized_existing.append((ticker, company_name, start_date, end_date))

        # Normalize list of codes to a deterministic sequence for processing
        self.existing_codes = normalized_existing

        # Determine persistence threshold (explicit > config > default)
        self.threshold = threshold or self.config.repository.persistence_threshold or 50

        # adapter para a estratégia
        def _adapter(items: List[StockQuoteDTO], *, uow: Uow) -> None:
            if save_callback is not None:
                save_callback(items, uow=uow)

        # Build a save strategy that buffers detail DTOs and flushes on threshold
        strategy: SaveStrategy[StockQuoteDTO] = SaveStrategy.from_config(
            _adapter if save_callback else None,
            self.threshold,
            config=self.config,
            uow_factory=self.uow_factory,
        )

        # Pair each entry with its index for progress reporting
        tasks = list(enumerate(self.existing_codes))

        # Mark the start time for progress ETA computations
        start_time = time.perf_counter()


        # Worker that processes a single company entry through the detail pipeline
        def processor(task: WorkerTaskDTO) -> List[StockQuoteDTO]:
            index = task.index
            entry = cast(StockQuoteExistingItem, task.data)
            worker_id = task.worker_id

            ticker, company_name, start_date, end_date = entry

            symbol = ticker.upper() if "." in ticker else f"{ticker.upper()}.SA"
            has_yahoo_ticker = self.has_yahoo_ticker(symbol, start_date, end_date)

            if not has_yahoo_ticker:
                extra_info = {
                    "ticker": ticker,
                    "company_name": company_name[:8],
                    }
                self.logger.log(
                    f"{ticker}",
                    level="info",
                    progress={
                        "index": index,
                        "size": len(tasks),
                        "start_time": start_time,
                    },
                    extra=extra_info,
                    worker_id=worker_id,
                )
                return []

            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=False,
                actions=False,
                group_by="column",
                threads=False,
            )

            if df is None or df.empty:
                return []

            # Se ainda vier MultiIndex por algum motivo raro
            if isinstance(df.columns, pd.MultiIndex):
                df = df.swaplevel(axis=1)[symbol]

            # garante ordenação por data
            df = df.sort_index()

            # Garanta índice temporal concreto
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index, errors="coerce", utc=True)
            df = df[df.index.notna()]

            memory_usage = df.memory_usage(deep=True)
            bytes_used = int(memory_usage.sum() if isinstance(memory_usage, pd.Series) else memory_usage)
            self._metrics_collector.add_network_bytes(bytes_used)

            first_index = pd.Timestamp(df.index[0])
            last_index = pd.Timestamp(df.index[-1])
            d_min = first_index.date()
            d_max = last_index.date()

            close_min = float(df.iloc[0]["Close"])
            close_max = float(df.iloc[-1]["Close"])

            out: list[StockQuoteDTO] = []

            for idx, row in df.iterrows():
                ts = cast(pd.Timestamp, idx)
                dto = StockQuoteDTO(
                    company_name=company_name,
                    ticker=ticker,
                    date=ts.to_pydatetime().replace(tzinfo=None),
                    open=row["Open"],
                    high=row["High"],
                    low=row["Low"],
                    close=row["Close"],
                    adj_close=row["Adj Close"],
                    volume=row["Volume"],
                    currency="BRL",
                )
                out.append(dto)

            # Prepare diagnostic metadata for logs
            extra_info = {
                "ticker": ticker,
                "company_name": company_name[:8],
                "start_date": d_min,
                "start_close": f"{close_min:.2f}",
                "end_date": d_max,
                "end_close": f"{close_max:.2f}",
                "download": self.byte_formatter.format_bytes(self._metrics_collector.download_bytes),
                "total_download": self.byte_formatter.format_bytes(self._metrics_collector.network_bytes),
            }
            # Emit structured progress log for this item
            self.logger.log(
                f"{ticker}",
                level="info",
                progress={
                    "index": index,
                    "size": len(tasks),
                    "start_time": start_time,
                },
                extra=extra_info,
                worker_id=worker_id,
            )

            return out


        # Handler that buffers items and triggers flushes via the strategy
        def handle_batch(batch: List[StockQuoteDTO]) -> None:
            for item in batch:
                strategy.handle(item)

        # Execute detail processing concurrently
        pool_results = self.worker_pool_executor.run(
            tasks=tasks,
            processor=processor,
            logger=self.logger,
            on_result=handle_batch,
            max_workers=self.config.worker_pool.max_workers or 1,
            total_size=len(tasks),
        )

        # Ensure any residual buffered items are flushed
        strategy.finalize()

        # Flatten nested worker results, skipping empty batches
        results: List[StockQuoteDTO] = [
            dto
            for batch in pool_results
            if batch
            for dto in batch
        ]

        # Return aggregated results and preserve execution metrics
        return results

    # def has_yahoo_ticker(self, symbol: str, start_date: datetime, end_date: datetime) -> bool:
    def has_yahoo_ticker(self, symbol: str, start_date: Optional[datetime], end_date: Optional[datetime]) -> bool:
        """Valida se um ticker possui dados disponíveis no intervalo informado."""
        # guarda de sanidade para o type checker e para a rede
        if start_date is None or end_date is None:
            return False
        if end_date <= start_date:
            return False
        """Valida se um ticker possui dados disponíveis no intervalo informado."""
        url = (
            f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
            f"?period1={calendar.timegm(start_date.utctimetuple())}"
            f"&period2={calendar.timegm(end_date.utctimetuple())}"
            f"&interval=1d"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            ),
            "Referer": "https://finance.yahoo.com/",
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            payload = response.json()
            if response.status_code != 200:
                return False

            indicators = payload.get("chart", {}).get("result", [{}])[0].get("indicators", {})
            quote = indicators.get("quote", [{}])[0]
            if not quote:
                return False
        except Exception:
            return False

        return True

    def get_metrics(self) -> int:
        return self._metrics_collector.network_bytes



    # def _save_date(self, val):
    #     if isinstance(val, pd.Series):
    #         val = val
    #     if isinstance(val, pd.Timestamp):
    #         return val.date()
    #     if isinstance(val, datetime):
    #         return val.date()
    #     if isinstance(val, date):
    #         return val
    #     return pd.to_datetime(val).date()


    # def _safe_float(self, val: object, default: float = 0.0) -> float:
    #     return default if pd.isna(val) else float(val)

    # def _safe_int(self, val: object, default: int = 0) -> int:
    #     return default if pd.isna(val) else int(val)


