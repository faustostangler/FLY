from __future__ import annotations

import hashlib
from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from application.services.indicator_normalizer_service import IndicatorNormalizerService
from domain.dtos.indicators_dto import IndicatorRecordDTO
from domain.dtos.normalized_series_dto import (
    NormalizedMetricSeriesDTO,
    NormalizedSeriesBundleDTO,
)
from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.dtos.stock_quote_dto import StockQuoteDTO


@dataclass(frozen=True)
class IndicatorFactorRule:
    """Describe how to transform an indicator into a multiplicative factor."""

    code: str
    output_code: str
    method: str  # "index" or "rate"
    scale: float = 1.0


class DailySeriesNormalizerService:
    """Expand financial, market, and macro series to a shared daily calendar."""

    def __init__(
        self,
        *,
        indicator_normalizer: IndicatorNormalizerService,
        indicator_factor_rules: Sequence[IndicatorFactorRule] | None = None,
    ) -> None:
        self._indicator_normalizer = indicator_normalizer
        self._indicator_factor_rules = {
            rule.code: rule for rule in indicator_factor_rules or ()
        }

    def normalize(
        self,
        *,
        company_id: str,
        statements: Sequence[StatementFetchedDTO],
        quotes: Sequence[StockQuoteDTO],
        indicators: Sequence[IndicatorRecordDTO],
    ) -> NormalizedSeriesBundleDTO:
        calendar = tuple(
            self._iter_calendar_bounds(
                statements=statements, quotes=quotes, indicators=indicators
            )
        )

        series_map: MutableMapping[str, NormalizedMetricSeriesDTO] = {}

        if calendar:
            series_map.update(
                self._normalize_statements(
                    company_id=company_id, statements=statements, calendar=calendar
                )
            )
            series_map.update(
                self._normalize_quotes(
                    company_id=company_id, quotes=quotes, calendar=calendar
                )
            )
            series_map.update(
                self._normalize_indicators(
                    company_id=company_id, indicators=indicators, calendar=calendar
                )
            )

        return NormalizedSeriesBundleDTO(
            company_id=company_id,
            calendar=calendar,
            series_map=dict(series_map),
        )

    @staticmethod
    def _iter_calendar(start: datetime, end: datetime) -> Iterable[datetime]:
        current = start
        while current <= end:
            yield current
            current += timedelta(days=1)

    def _iter_calendar_bounds(
        self,
        *,
        statements: Sequence[StatementFetchedDTO],
        quotes: Sequence[StockQuoteDTO],
        indicators: Sequence[IndicatorRecordDTO],
    ) -> Iterable[datetime]:
        start, end = self._determine_bounds(
            statements=statements, quotes=quotes, indicators=indicators
        )
        if start is None or end is None:
            return ()
        return self._iter_calendar(start, end)

    @staticmethod
    def _determine_bounds(
        *,
        statements: Sequence[StatementFetchedDTO],
        quotes: Sequence[StockQuoteDTO],
        indicators: Sequence[IndicatorRecordDTO],
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        start: Optional[datetime] = None
        end: Optional[datetime] = None

        def update_bounds(candidate: Optional[datetime]) -> None:
            nonlocal start, end
            if candidate is None:
                return
            if start is None or candidate < start:
                start = candidate
            if end is None or candidate > end:
                end = candidate

        for row in statements:
            update_bounds(row.quarter)

        for quote in quotes:
            update_bounds(quote.date)

        for record in indicators:
            update_bounds(record.date)

        return start, end

    def _normalize_statements(
        self,
        *,
        company_id: str,
        statements: Sequence[StatementFetchedDTO],
        calendar: Tuple[datetime, ...],
    ) -> Mapping[str, NormalizedMetricSeriesDTO]:
        grouped: Dict[str, Dict[datetime, tuple[float | None, str | None, str | None]]] = {}
        for row in statements:
            if row.quarter is None:
                continue
            account = str(row.account or "").strip()
            if not account:
                continue
            value = float(row.value) if row.value is not None else None
            version = str(row.version) if row.version is not None else None
            digest = self._hash_parts(
                company_id,
                "statement",
                account,
                row.quarter.isoformat(),
                value,
                version,
            )
            grouped.setdefault(account, {})[row.quarter] = (value, version, digest)

        series: Dict[str, NormalizedMetricSeriesDTO] = {}
        for account, points in grouped.items():
            filled = self._fill_series(calendar, points)
            series[account] = NormalizedMetricSeriesDTO(
                company_id=company_id,
                metric_code=account,
                calendar=calendar,
                values=filled[0],
                versions=filled[1],
                hashes=filled[2],
                source="statement",
            )
        return series

    def _normalize_quotes(
        self,
        *,
        company_id: str,
        quotes: Sequence[StockQuoteDTO],
        calendar: Tuple[datetime, ...],
    ) -> Mapping[str, NormalizedMetricSeriesDTO]:
        metrics: Dict[str, Dict[datetime, tuple[float | None, str | None, str | None]]] = {}

        for quote in quotes:
            date = quote.date
            version = date.date().isoformat()
            entries = {
                "QUOTE.CLOSE": quote.close,
                "QUOTE.ADJ_CLOSE": quote.adj_close,
                f"QUOTE.{quote.ticker}.CLOSE": quote.close,
                f"QUOTE.{quote.ticker}.ADJ_CLOSE": quote.adj_close,
            }
            for metric_code, raw_value in entries.items():
                if raw_value is None:
                    continue
                value = float(raw_value)
                digest = self._hash_parts(
                    company_id,
                    "quote",
                    metric_code,
                    date.isoformat(),
                    value,
                    quote.ticker,
                )
                bucket = metrics.setdefault(metric_code, {})
                bucket[date] = (value, version, digest)

        series: Dict[str, NormalizedMetricSeriesDTO] = {}
        for metric_code, points in metrics.items():
            if not points:
                continue
            filled = self._fill_series(calendar, points)
            series[metric_code] = NormalizedMetricSeriesDTO(
                company_id=company_id,
                metric_code=metric_code,
                calendar=calendar,
                values=filled[0],
                versions=filled[1],
                hashes=filled[2],
                source="stock_quote",
            )
        return series

    def _normalize_indicators(
        self,
        *,
        company_id: str,
        indicators: Sequence[IndicatorRecordDTO],
        calendar: Tuple[datetime, ...],
    ) -> Mapping[str, NormalizedMetricSeriesDTO]:
        normalized = self._indicator_normalizer.normalize(indicators)

        grouped: Dict[str, Dict[datetime, tuple[float | None, str | None, str | None]]] = {}
        for record in normalized:
            date = record.date
            code = record.code
            value = float(record.value) if record.value is not None else None
            version = date.isoformat()
            digest = self._hash_parts(
                company_id,
                record.source,
                code,
                date.isoformat(),
                value,
                version,
            )
            grouped.setdefault(code, {})[date] = (value, version, digest)

        base_series: Dict[str, NormalizedMetricSeriesDTO] = {}
        for code, points in grouped.items():
            filled = self._fill_series(calendar, points)
            base_series[code] = NormalizedMetricSeriesDTO(
                company_id=company_id,
                metric_code=code,
                calendar=calendar,
                values=filled[0],
                versions=filled[1],
                hashes=filled[2],
                source="indicator",
            )

        derived = self._build_indicator_factors(base_series)

        merged: Dict[str, NormalizedMetricSeriesDTO] = {}
        merged.update(base_series)
        merged.update(derived)
        return merged

    def _build_indicator_factors(
        self, base_series: Mapping[str, NormalizedMetricSeriesDTO]
    ) -> Mapping[str, NormalizedMetricSeriesDTO]:
        derived: Dict[str, NormalizedMetricSeriesDTO] = {}
        for code, rule in self._indicator_factor_rules.items():
            series = base_series.get(code)
            if series is None:
                continue
            factor_values: List[float | None] = []
            base_value: float | None = None
            cumulative = 1.0
            for value in series.values:
                if rule.method == "index":
                    if base_value is None and value is not None and value != 0:
                        base_value = value
                    if base_value in (None, 0) or value is None:
                        factor_values.append(None if not factor_values else factor_values[-1])
                    else:
                        factor_values.append(value / base_value)
                elif rule.method == "rate":
                    if value is None:
                        factor_values.append(cumulative)
                    else:
                        cumulative *= 1 + (value * rule.scale)
                        factor_values.append(cumulative)
                else:
                    factor_values.append(None)
            derived[rule.output_code] = NormalizedMetricSeriesDTO(
                company_id=series.company_id,
                metric_code=rule.output_code,
                calendar=series.calendar,
                values=tuple(factor_values),
                versions=series.versions,
                hashes=series.hashes,
                source="indicator",
            )
        return derived

    @staticmethod
    def _hash_parts(*parts: object) -> str:
        payload = "|".join("" if part is None else str(part) for part in parts)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _fill_series(
        calendar: Tuple[datetime, ...],
        points: Mapping[datetime, tuple[float | None, str | None, str | None]],
    ) -> Tuple[Tuple[float | None, ...], Tuple[str | None, ...], Tuple[str | None, ...]]:
        if not points:
            size = len(calendar)
            empty: Tuple[float | None, ...] = tuple(None for _ in range(size))
            none_str: Tuple[str | None, ...] = tuple(None for _ in range(size))
            return empty, none_str, none_str

        ordered_dates = sorted(points.keys())
        values: List[float | None] = []
        versions: List[str | None] = []
        hashes: List[str | None] = []

        for day in calendar:
            idx = bisect_right(ordered_dates, day) - 1
            if idx < 0:
                idx = 0
            elif idx >= len(ordered_dates):
                idx = len(ordered_dates) - 1
            key = ordered_dates[idx]
            value, version, digest = points[key]
            values.append(value)
            versions.append(version)
            hashes.append(digest)

        return tuple(values), tuple(versions), tuple(hashes)
