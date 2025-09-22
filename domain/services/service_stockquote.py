from typing import Any

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.usecases.sync_stock_quote import SyncStockQuoteUseCase
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.scraper_stock_quote_port import ScraperStockQuotePort


class StockQuoteService:
    """Service layer to coordinate company-related synchronization use cases."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        repository: RepositoryStockQuotePort,
        scraper: ScraperStockQuotePort,
        uow_factory: UowFactoryPort,
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

        self.uow_factory = uow_factory

        # Initialize the use case responsible for company synchronization
        self.sync_stock_quote_usecase = SyncStockQuoteUseCase(
            config=self.config,
            logger=self.logger,
            repository=repository,
            scraper=scraper,
            uow_factory=self.uow_factory,
            max_workers=self.config.worker_pool.max_workers,
        )

    def __call__(self, *args: Any, **kwds: Any) -> SyncResultsDTO:
        return self.run()

    def run(self) -> SyncResultsDTO:
        """Trigger company synchronization workflow.

        Returns:
            Any: The result of the synchronization use case execution.
        """
        # Delegate execution to the underlying use case
        return self.sync_stock_quote_usecase()
