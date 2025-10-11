from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping, Sequence, Tuple


@dataclass(frozen=True, kw_only=True)
class NormalizedMetricSeriesDTO:
    """Daily view of a single metric after calendar normalization."""

    company_id: str
    metric_code: str
    calendar: Tuple[datetime, ...]
    values: Tuple[float | None, ...]
    versions: Tuple[str | None, ...]
    hashes: Tuple[str | None, ...]
    source: str

    def __post_init__(self) -> None:
        size = len(self.calendar)
        if not (
            len(self.values) == len(self.versions) == len(self.hashes) == size
        ):
            raise ValueError("Normalized series arrays must share the same length")

    @property
    def length(self) -> int:
        return len(self.calendar)

    def iter_rows(self) -> Iterable[tuple[datetime, float | None, str | None, str | None]]:
        return zip(self.calendar, self.values, self.versions, self.hashes)


@dataclass(frozen=True, kw_only=True)
class NormalizedSeriesBundleDTO:
    """Collection of normalized metric series sharing a daily calendar."""

    company_id: str
    calendar: Tuple[datetime, ...]
    series_map: Mapping[str, NormalizedMetricSeriesDTO]

    def __post_init__(self) -> None:
        for metric, series in self.series_map.items():
            if series.calendar != self.calendar:
                raise ValueError(
                    "All normalized series must share the bundle calendar"
                )
            if series.metric_code != metric:
                raise ValueError(
                    "Series map keys must match the contained metric codes"
                )

    def get(self, metric_code: str) -> NormalizedMetricSeriesDTO | None:
        return self.series_map.get(metric_code)

    def required(self, metric_code: str) -> NormalizedMetricSeriesDTO:
        series = self.get(metric_code)
        if series is None:
            raise KeyError(metric_code)
        return series

    def keys(self) -> Sequence[str]:
        return tuple(self.series_map.keys())

    def __len__(self) -> int:
        return len(self.calendar)
