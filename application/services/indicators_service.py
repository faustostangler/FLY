from __future__ import annotations

from collections.abc import Mapping

from application.ports.indicator_processor_port import IndicatorProcessorPort
from domain.dtos.indicator_dto import IndicatorRecordDTO
from domain.dtos.sync_results_dto import SyncResultsDTO


class IndicatorsService:
    """Coordinate synchronization of economic indicators across sources."""

    def __init__(self, processors: Mapping[str, IndicatorProcessorPort]) -> None:
        self._processors = dict(processors)

    def available_sources(self) -> tuple[str, ...]:
        """Expose the registered indicator sources."""

        return tuple(self._processors)

    def run(self, source: str) -> SyncResultsDTO[IndicatorRecordDTO]:
        """Trigger synchronization for a single source."""

        processor = self._processors[source]
        return processor.run()
