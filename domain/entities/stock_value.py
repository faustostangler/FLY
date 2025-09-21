from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import FrozenSet


@dataclass(frozen=True)
class Ticker:
    """Value object representing a ticker without exchange suffix."""
    code: str


@dataclass(frozen=True)
class Company:
    """Immutable company aggregate with its tradable tickers."""
    id: str
    name: str
    has_isin: bool
    tickers: FrozenSet[Ticker]


@dataclass(frozen=True)
class Quote:
    """Domain representation of a historical quote (OHLC + adjusted close)."""
    ticker: Ticker
    date: date
    open: float
    high: float
    low: float
    close: float
    close_adj: float
    volume: int
