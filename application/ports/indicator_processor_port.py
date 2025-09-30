from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from domain.dtos.indicator_dto import IndicatorRawDTO, IndicatorRecordDTO
from domain.dtos.sync_results_dto import SyncResultsDTO


class IndicatorProcessorPort(ABC):
    """Processor contract that defines the load/transform/persist workflow."""

    @abstractmethod
    def run(self) -> SyncResultsDTO[IndicatorRecordDTO]:
        """Execute the full processing pipeline for an indicator source."""

    @abstractmethod
    def load(self) -> Iterable[IndicatorRawDTO]:
        """Load raw datapoints from the configured source."""

    @abstractmethod
    def transform(
        self, raw_entries: Iterable[IndicatorRawDTO]
    ) -> Iterable[IndicatorRecordDTO]:
        """Normalize raw datapoints into standardized indicator records."""

    @abstractmethod
    def persist(self, records: Iterable[IndicatorRecordDTO]) -> SyncResultsDTO[IndicatorRecordDTO]:
        """Persist the normalized records and return synchronization metadata."""
