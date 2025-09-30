from __future__ import annotations

from collections.abc import Iterable, Sequence

from domain.dtos.indicator_dto import IndicatorRecordDTO
from domain.ports.repository_indicator_port import RepositoryIndicatorPort


class IndicatorRepository(RepositoryIndicatorPort):
    """Persistence adapter for indicator datapoints."""

    def list_existing_codes(self, origin: str) -> Sequence[str]:
        raise NotImplementedError

    def upsert_many(self, records: Iterable[IndicatorRecordDTO]) -> None:
        raise NotImplementedError
