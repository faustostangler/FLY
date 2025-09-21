# application/services/stock_value.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from application.ports.stock_value import (
    CompaniesReaderPort,
    PriceFeedPort,
    QuotesWriterPort,
)
from domain.services.price_series_service import PriceSeriesService


@dataclass
class StockValueService:
    """Application service orchestrating the stock-value workflow."""

    companies_repo: CompaniesReaderPort
    quotes_repo: QuotesWriterPort
    price_feed: PriceFeedPort
    price_series_service: PriceSeriesService

    def __call__(self) -> None:
        return self.run()

    def run(self) -> None:
        """Fetch daily prices and persist aggregated quotes."""

        for company in self.companies_repo.load_companies_with_stock():
            if not company.has_isin:
                continue
            for ticker in sorted(company.tickers, key=lambda tk: tk.code):
                daily = self.price_feed.download_daily(ticker)
                if daily.empty:
                    continue
                quarterly_quotes = self.price_series_service.quarterly_quotes(
                    ticker, daily
                )
                if not quarterly_quotes:
                    continue
                self.quotes_repo.upsert_quotes(quarterly_quotes)
