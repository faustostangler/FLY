# infrastructure/adapters/scraper_stock_quote.py
from __future__ import annotations
from datetime import date
from typing import Iterable, Iterator, Optional, Sequence, Any, List

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
        uow: Uow = kwargs.get("uow")
        http_client: AffinityHttpClientPort = kwargs.get("http_client")

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}.SA"

        with http_client.borrow_session() as session:
            resp = http_client.fetch_with(session, url, headers=session.headers)
        data = resp.json()


        df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
        if df is None or df.empty:
            return []

        df = df.rename(columns={"Adj Close": "AdjClose"}).reset_index()

        items: list[StockQuoteDTO] = []
        for _, row in df.iterrows():
            d = getattr(row["Date"], "date", lambda: row["Date"])()
            dto = StockQuoteDTO(
                company_name=company_name,
                ticker=ticker,
                date=d,
                open=float(row.get("Open") or 0.0),
                high=float(row.get("High") or 0.0),
                low=float(row.get("Low") or 0.0),
                close=float(row.get("Close") or 0.0),
                adj_close=float(row.get("AdjClose") or row.get("Adj Close") or 0.0),
                volume=int(row.get("Volume") or 0),
                currency="BRL",
            )
            items.append(dto)

            # flush incremental
            if save_callback and uow and threshold and len(items) >= threshold:
                save_callback(items, uow=uow)
                items.clear()

        # flush final
        if save_callback and uow and items:
            save_callback(items, uow=uow)

        return items

    @property
    def metrics_collector(self) -> MetricsCollectorPort:
        """Metrics collector used by the scraper."""
        return self._metrics_collector

    def get_metrics(self) -> int:
        return self._metrics_collector.network_bytes
