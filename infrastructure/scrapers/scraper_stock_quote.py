# infrastructure/adapters/scraper_stock_quote.py
from __future__ import annotations
from datetime import datetime, date
import pandas as pd
from typing import Iterable, Iterator, Optional, Sequence, Any, List

import requests
import yfinance as yf  # dependência de infraestrutura

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.metrics_collector_port import MetricsCollectorPort
from application.ports.http_client_port import AffinityHttpClientPort
from application.ports.uow_port import Uow
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.scraper_base_port import SaveCallback
from domain.ports.scraper_stock_quote_port import ScraperStockQuotePort

class StockQuoteScraper(ScraperStockQuotePort):
    """Scraper de cotações com delta por ticker e saída em DTO."""

    def __init__(
        self,
        *,
        config: ConfigPort,
        logger: LoggerPort,
        repository_stock_quote: RepositoryStockQuotePort,
        metrics_collector: MetricsCollectorPort,
    ) -> None:
        self.config = config
        self.logger = logger
        self.repository_stock_quote = repository_stock_quote
        self._metrics_collector = metrics_collector

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        existing_codes: Optional[List[str]] = None,
        save_callback: Optional[SaveCallback[StockQuoteDTO]] = None,
        **kwargs,
    ) -> List[StockQuoteDTO]:
        """Stream de DTOs de `start..end` e persistência opcional em lotes."""
        ticker, company_name = kwargs.get("data")
        start_date: date = kwargs.get("start_date").isoformat()
        end_date: date = kwargs.get("end_date").isoformat()

        symbol = ticker.upper() if "." in ticker else f"{ticker.upper()}.SA"

        # probe simples para evitar consent/blocked
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/115.0.0.0 Safari/537.36",
            "Referer": "https://finance.yahoo.com/",
        }
        try:
            r = requests.get(url, headers=headers)
            _ = r.json()  # não use raise_for_status
            if r.status_code != 200:
                return []
        except Exception:
            return []

        if r.status_code != 200:
            return []
        # if not data:
        #     return []

        df = yf.download(
            symbol,
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=False,
        )
        if df is None or df.empty:
            return []

        if isinstance(df.columns, pd.MultiIndex):
            df = df.swaplevel(axis=1)[symbol]

        # garante ordenação por data
        df = df.sort_index()

        d_min = df.index[0].date()
        d_max = df.index[-1].date()

        close_min = float(df.iloc[0]["Close"])
        close_max = float(df.iloc[-1]["Close"])

        out: list[StockQuoteDTO] = []

        for idx, row in df.iterrows():
            dto = StockQuoteDTO(
                company_name=company_name,
                ticker=ticker,
                date=idx.date(),
                open=row["Open"],
                high=row["High"],
                low=row["Low"],
                close=row["Close"],
                adj_close=row["Adj Close"],
                volume=row["Volume"],
                currency="BRL",
            )
            out.append(dto)

        if save_callback is not None:
            uow: Uow | None = kwargs.get("uow")
            save_callback(out, uow=uow)  # type: ignore[arg-type]

        self.logger.log(
            f"{ticker} {d_min} to {d_max} {company_name} {close_min:.2f} {close_max:.2f}",
            level="info",
        )

        return out

    def _save_date(self, val):
        if isinstance(val, pd.Series):
            val = val
        if isinstance(val, pd.Timestamp):
            return val.date()
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val
        return pd.to_datetime(val).date()


    def _safe_float(self, val: object, default: float = 0.0) -> float:
        return default if pd.isna(val) else float(val)

    def _safe_int(self, val: object, default: int = 0) -> int:
        return default if pd.isna(val) else int(val)


    @property
    def metrics_collector(self) -> MetricsCollectorPort:
        """Metrics collector used by the scraper."""
        return self._metrics_collector

    def get_metrics(self) -> int:
        return self._metrics_collector.network_bytes

