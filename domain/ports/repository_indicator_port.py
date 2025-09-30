from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol

from domain.dtos.indicator_dto import IndicatorRecordDTO


class RepositoryIndicatorPort(Protocol):
    """Repository boundary for persisting normalized indicator datapoints."""

    def list_existing_codes(self, origin: str) -> Sequence[str]:
        """Return the set of indicator codes already stored for the origin."""

    def upsert_many(self, records: Iterable[IndicatorRecordDTO]) -> None:
        """Persist a batch of normalized indicator datapoints atomically."""
