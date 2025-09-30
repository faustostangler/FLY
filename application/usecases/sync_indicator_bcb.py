from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.ports.indicator_processor_port import IndicatorProcessorPort
from domain.dtos.indicator_dto import IndicatorRawDTO, IndicatorRecordDTO
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.ports.repository_indicator_port import RepositoryIndicatorPort
from domain.ports.scraper_indicator_bcb_port import ScraperIndicatorBcbPort


class SyncIndicatorBcbUseCase(IndicatorProcessorPort):
    """Use case for synchronizing indicators from Banco Central do Brasil."""

    def __init__(
        self,
        *,
        config: ConfigPort,
        logger: LoggerPort,
        repository: RepositoryIndicatorPort,
        scraper: ScraperIndicatorBcbPort,
        uow_factory: UowFactoryPort,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> None:
        self.config = config
        self.logger = logger
        self.repository = repository
        self.scraper = scraper
        self.uow_factory = uow_factory
        self.start_date = start_date
        self.end_date = end_date

    def run(self) -> SyncResultsDTO[IndicatorRecordDTO]:
        raise NotImplementedError

    def load(self) -> Iterable[IndicatorRawDTO]:
        raise NotImplementedError

    def transform(self, raw_entries: Iterable[IndicatorRawDTO]) -> Iterable[IndicatorRecordDTO]:
        raise NotImplementedError

    def persist(self, records: Iterable[IndicatorRecordDTO]) -> SyncResultsDTO[IndicatorRecordDTO]:
        raise NotImplementedError
