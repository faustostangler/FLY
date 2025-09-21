# infrastructure/gateways/yfinance_gateway.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, List

import pandas as pd
import yfinance as yf

from application.ports.stock_value import PriceFeedPort
from domain.entities.stock_value import Ticker


@dataclass
class YFinanceGateway(PriceFeedPort):
    """Adapter that wraps ``yfinance.download`` and normalizes its output."""

    suffix: str = ".SA"
    max_days_per_request: int | None = None
    today_provider: Callable[[], date] = date.today

    def download_daily(self, ticker: Ticker, start: date) -> pd.DataFrame:
        symbol = f"{ticker.code}{self.suffix}" if self.suffix else ticker.code
        end_date = self.today_provider()
        if start > end_date:
            return pd.DataFrame(columns=["value"])

        frames = self._download_in_chunks(symbol, start, end_date)
        if not frames:
            return pd.DataFrame(columns=["value"])

        combined = pd.concat(frames) if len(frames) > 1 else frames[0]
        if combined.empty:
            return pd.DataFrame(columns=["value"])

        combined.index = pd.to_datetime(combined.index).tz_localize(None)
        combined = combined[~combined.index.duplicated(keep="last")]  # de-dup merges
        combined.sort_index(inplace=True)
        return combined

    def _download_in_chunks(self, symbol: str, start: date, end: date) -> List[pd.DataFrame]:
        frames: List[pd.DataFrame] = []
        if not self.max_days_per_request:
            frame = self._download(symbol, start, end)
            if not frame.empty:
                frames.append(frame)
            return frames

        current = start
        while current <= end:
            chunk_end = min(end, current + timedelta(days=self.max_days_per_request - 1))
            frame = self._download(symbol, current, chunk_end)
            if not frame.empty:
                frames.append(frame)
            current = chunk_end + timedelta(days=1)
        return frames

    def _download(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        raw = yf.download(
            symbol,
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
            progress=False,
            group_by="ticker",
        )
        if raw.empty:
            return pd.DataFrame(columns=["value"])

        if isinstance(raw.columns, pd.MultiIndex):
            try:
                raw.columns = raw.columns.droplevel("Ticker")
            except KeyError:
                raw.columns = raw.columns.droplevel(-1)

        series = raw.get("Adj Close")
        if series is None:
            series = raw.get("Close")
        if series is None:
            return pd.DataFrame(columns=["value"])

        frame = pd.DataFrame({"value": series})
        return frame
