# application/ports/stock_value.py
from __future__ import annotations

from datetime import date
from typing import Iterable, Protocol

import pandas as pd

from domain.entities.stock_value import Company, Quote, Ticker


class CompaniesReaderPort(Protocol):
    """Port for loading companies eligible for price synchronization."""

    def load_companies_with_stock(self) -> Iterable[Company]:
        ...


class QuotesWriterPort(Protocol):
    """Port for persisting normalized quote series."""

    def upsert_quotes(self, quotes: Iterable[Quote]) -> None:
        ...


class PriceFeedPort(Protocol):
    """Port abstracting the external price provider (e.g., yfinance)."""

    def download_daily(self, ticker: Ticker, start: date) -> pd.DataFrame:
        ...
