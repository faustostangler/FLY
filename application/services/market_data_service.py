# application/services/market_data_service.py
from __future__ import annotations

from datetime import date
from typing import Iterable, Optional

from application.ports.market_data_port import MarketDataPort
from application.ports.price_lookup_port import PriceLookupPort
from infrastructure.repositories.market_quote_repository import MarketQuoteRepository


def quarter_start(quarter_end: date) -> date:
    y = quarter_end.year
    if quarter_end.month == 3:
        return date(y, 1, 1)
    if quarter_end.month == 6:
        return date(y, 4, 1)
    if quarter_end.month == 9:
        return date(y, 7, 1)
    if quarter_end.month == 12:
        return date(y, 10, 1)
    m = ((quarter_end.month - 1 - 3) % 12) + 1
    y2 = y if quarter_end.month > 3 else y - 1
    return date(y2, m, 1)


class MarketDataService(PriceLookupPort):
    def __init__(self, port: MarketDataPort, repo: MarketQuoteRepository):
        self.port = port
        self.repo = repo

    def ensure_series_for_quarters(self, symbol: str, quarter_ends: Iterable[date]) -> None:
        ranges = [(quarter_start(qe), qe) for qe in quarter_ends]
        if not ranges:
            return
        start = min(r[0] for r in ranges)
        end = max(r[1] for r in ranges)
        quotes = self.port.fetch_window(symbol, start, end)
        self.repo.bulk_upsert(quotes)

    def price_at_quarter_end(self, symbol: str, quarter_end: date) -> Optional[float]:
        quote = self.repo.latest_on_or_before(symbol, quarter_end)
        return None if quote is None else quote.adjusted_close

    def series_of_quarter(self, symbol: str, quarter_end: date):
        start = quarter_start(quarter_end)
        return self.repo.get_between(symbol, start, quarter_end)
