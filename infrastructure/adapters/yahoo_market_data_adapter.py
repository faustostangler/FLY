# infrastructure/adapters/yahoo_market_data_adapter.py

from __future__ import annotations

import datetime as dt
import time
from typing import Callable, Sequence

import yfinance as yf

from application.ports.market_data_port import MarketDataPort
from domain.dto.market_quote_dto import MarketQuoteDTO


class YahooMarketDataAdapter(MarketDataPort):
    def __init__(self, symbol_mapper: Callable[[str], str], currency: str = "BRL"):
        self.provider = "yahoo"
        self.map_symbol = symbol_mapper
        self.currency = currency

    def fetch_window(self, symbol: str, start: dt.date, end: dt.date) -> Sequence[MarketQuoteDTO]:
        ysym = self.map_symbol(symbol)
        ystart = start.isoformat()
        yend = (end + dt.timedelta(days=1)).isoformat()
        for attempt in range(4):
            try:
                df = yf.download(
                    ysym,
                    start=ystart,
                    end=yend,
                    auto_adjust=True,
                    progress=False,
                    threads=False,
                )
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(1.5 * (attempt + 1))
        else:
            df = None
        if df is None or df.empty:
            return []
        out: list[MarketQuoteDTO] = []
        for idx, row in df.iterrows():
            day = idx.date()
            close = float(row["Close"])
            out.append(
                MarketQuoteDTO(self.provider, symbol, day, close, close, self.currency)
            )
        return out
