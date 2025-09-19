# application/ports/market_data_port.py

from typing import Sequence, Protocol
from datetime import date

from domain.dtos.market_quote_dto import MarketQuoteDTO


class MarketDataPort(Protocol):
    def fetch_window(self, symbol: str, start: date, end: date) -> Sequence[MarketQuoteDTO]: ...