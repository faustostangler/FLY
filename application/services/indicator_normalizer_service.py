from __future__ import annotations

from typing import Iterable, List

from domain.dtos.indicators_dto import IndicatorRecordDTO


class IndicatorNormalizerService:
    """Convert indicator observations to a daily calendar."""

    def normalize(self, records: Iterable[IndicatorRecordDTO]) -> List[IndicatorRecordDTO]:
        normalized = [record for record in records if record is not None]
        normalized.sort(key=lambda item: (item.source, item.code, item.date))
        return normalized
