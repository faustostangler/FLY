from __future__ import annotations

from datetime import date
from typing import List, Sequence, Tuple

from application.ports.market_data_port import MarketDataPort
from domain.dtos.market_quote_dto import MarketQuoteDTO


class CompositeMarketDataAdapter(MarketDataPort):
    """Combine multiple market data providers, preferring earlier ones."""

    def __init__(self, providers: Sequence[MarketDataPort]) -> None:
        self.providers = tuple(providers)

    def fetch_window(
        self, symbol: str, start: date, end: date
    ) -> Sequence[MarketQuoteDTO]:
        seen: set[Tuple[date, str]] = set()
        collected: List[MarketQuoteDTO] = []
        for provider in self.providers:
            for quote in provider.fetch_window(symbol, start, end):
                if quote.day < start or quote.day > end:
                    continue
                key = (quote.day, quote.symbol)
                if key in seen:
                    continue
                seen.add(key)
                collected.append(quote)
        collected.sort(key=lambda q: q.day)
        return collected
