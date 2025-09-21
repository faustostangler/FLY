# domain/polices/quarter_median_policy.py
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class QuarterMedianPolicy:
    """Aggregate a daily price series into quarterly medians."""

    def aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a DataFrame with quarterly medians.

        Args:
            df: DataFrame indexed by datetime with a ``value`` column.

        Returns:
            DataFrame with columns ``quarter`` (``datetime.date``) and ``median``.
        """

        if df.empty:
            return pd.DataFrame(columns=["quarter", "median"])

        index = pd.to_datetime(df.index).tz_localize(None)
        normalized = df.copy()
        normalized.index = index
        quarters = pd.Series(index.to_period("Q"), index=index, name="quarter")
        medians = normalized.assign(quarter=quarters).groupby("quarter")["value"].median()
        end_dates = medians.index.map(lambda period: period.end_time.date())

        return pd.DataFrame({"quarter": list(end_dates), "median": medians.values})
