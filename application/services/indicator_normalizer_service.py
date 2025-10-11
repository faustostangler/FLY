from __future__ import annotations

from typing import Iterable, List

from domain.dtos.indicators_dto import IndicatorRecordDTO
from domain.value_objects.indicators import Coverage, Frequency


class IndicatorNormalizerService:
    """Convert indicator observations to a daily calendar."""

    def normalize(self, records: Iterable[IndicatorRecordDTO]) -> List[IndicatorRecordDTO]:
        normalized: list[IndicatorRecordDTO] = []
        for record in records:
            normalized.extend(self._normalize_record(record))
        normalized.sort(key=lambda item: (item.source, item.code, item.observation_date))
        return normalized

    def _normalize_record(self, record: IndicatorRecordDTO) -> List[IndicatorRecordDTO]:
        if record.frequency is Frequency.DAILY:
            return [record]

        period_days = record.observation_period.iter_days()
        if not period_days:
            return []

        if record.coverage is Coverage.FLOW and record.observation_period.days_count > 0:
            per_day_value = record.value / record.observation_period.days_count
        else:
            per_day_value = record.value

        availability_date = max(record.availability_date, record.observation_date)

        return [
            record.to_daily(day, value=per_day_value, availability_date=availability_date)
            for day in period_days
        ]
