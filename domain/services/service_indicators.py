from typing import Any

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.ports.uow_port import UowFactoryPort
from application.ports.http_client_port import AffinityHttpClientPort
from application.usecases.sync_bcb_indicators import SyncBCBIndicatorUseCase
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.dtos.indicators_dto import IndicatorRecordDTO
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.scraper_indicators_port import ScraperIndicatorsPort


class IndicatorsService:
    """Service layer to coordinate company-related synchronization use cases."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,

        repository_indicators: RepositoryIndicatorsPort,
        scraper_indicators: ScraperIndicatorsPort,

        uow_factory: UowFactoryPort,
        # http_client: AffinityHttpClientPort,
    ):
        """Initialize the service with required dependencies.

        Args:
            config (ConfigPort): Provides application configuration settings.
            logger (LoggerPort): Logging interface for tracking operations.
            repository (RepositoryCompanyDataPort): Repository for persisting company data.
            scraper (ScraperCompanyDataPort): Scraper for fetching company data.
        """
        # Keep references to injected dependencies
        self.logger = logger
        self.config = config

        self.repository_indicators = repository_indicators
        self.scraper_indicators = scraper_indicators

        self.uow_factory = uow_factory
        # self.http_client = http_client

        # Initialize the use case responsible for company synchronization
        self.sync_bcb_indicator_usecase = SyncBCBIndicatorUseCase(
            config=self.config,
            logger=self.logger,

            repository_indicators=self.repository_indicators,
            scraper_indicators=self.scraper_indicators,

            uow_factory=self.uow_factory,
            # http_client=self.http_client,

            # max_workers=self.config.worker_pool.max_workers,
        )

    def __call__(self, *args: Any, **kwds: Any) -> SyncResultsDTO:
        return self.run()

    def run(self) -> SyncResultsDTO[IndicatorRecordDTO]:
        """Trigger company synchronization workflow.

        Returns:
            Any: The result of the synchronization use case execution.
        """
        return self.sync_bcb_indicator_usecase()

        # with self.uow_factory() as uow:
        #     codes = self._get_tickers(uow)

        # code_stream = self.sync_stock_quote_usecase.stream_codes(codes)

        # results = self.worker_pool(
        #     logger=self.logger,
        #     tasks=enumerate(code_stream),
        #     processor=self.sync_stock_quote_usecase,
        #     total_size=len(codes)
        # )

        # items = list(results) if results is not None else []
        # return SyncResultsDTO[StockQuoteDTO](items=items, metrics=len(items))
        # # Delegate execution to the underlying use case
        # return self.sync_stock_quote_usecase()

