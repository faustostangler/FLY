# domain/services/price_series_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from domain.entities.stock_value import Quote, Ticker
from domain.polices.quarter_median_policy import QuarterMedianPolicy


@dataclass(frozen=True)
class PriceSeriesService:
    """Pure domain service for price-series transformations."""

    quarter_policy: QuarterMedianPolicy

    def quarterly_quotes(self, ticker: Ticker, daily: pd.DataFrame) -> List[Quote]:
        """Convert a daily price series into quarterly median quotes."""

        if daily.empty:
            return []

        aggregated = self.quarter_policy.aggregate(daily)
        quotes: List[Quote] = []
        for _, row in aggregated.iterrows():
            value = row["median"]
            if pd.isna(value):
                continue
            quarter_date = row["quarter"]
            if isinstance(quarter_date, pd.Timestamp):
                quarter_date = quarter_date.date()
            quotes.append(Quote(ticker=ticker, date=quarter_date, close_adj=float(value)))
        return quotes

    def daily_quotes(self, ticker: Ticker, daily: pd.DataFrame) -> List[Quote]:
        """Normalize raw daily data into :class:`Quote` objects."""

        if daily.empty:
            return []

        quotes: List[Quote] = []
        series = daily["value"] if "value" in daily else daily.squeeze()
        for idx, value in series.items():
            if pd.isna(value):
                continue
            if isinstance(idx, pd.Timestamp):
                idx = idx.tz_localize(None)
            quotes.append(Quote(ticker=ticker, date=idx.date(), close_adj=float(value)))
        return quotes
