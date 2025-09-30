from __future__ import annotations

from application.services.indicators_service import IndicatorsService
from application.ports.logger_port import LoggerPort
from domain.dtos.indicator_dto import IndicatorRecordDTO
from domain.dtos.sync_results_dto import SyncResultsDTO


class IndicatorsController:
    """Presentation layer coordinator for indicator synchronization."""

    def __init__(self, *, logger: LoggerPort, service: IndicatorsService) -> None:
        self._logger = logger
        self._service = service

    def sync(self, source: str) -> SyncResultsDTO[IndicatorRecordDTO]:
        """Trigger synchronization for the requested source."""

        self._logger.log(f"Syncing indicators for source={source}", level="info")
        return self._service.run(source)
