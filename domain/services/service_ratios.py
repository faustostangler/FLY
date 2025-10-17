from typing import Any

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.ports.uow_port import UowFactoryPort
from application.ports.http_client_port import AffinityHttpClientPort
from application.usecases.normalize_ratios import NormalizeUseCase
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
from domain.ports.repository_statements_ratio_port import RepositoryStatementRatioPort
from domain.ports.scraper_stock_quote_port import ScraperStockQuotePort


class RatiosService:
    """Service layer to coordinate company-related synchronization use cases."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,

        repository_company: RepositoryCompanyDataPort,
        repository_stock_quote: RepositoryStockQuotePort,
        repository_indicators: RepositoryIndicatorsPort,
        repository_statements_fetched: RepositoryStatementFetchedPort,
        repository_statements_ratio: RepositoryStatementRatioPort,

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

        self.repository_company = repository_company
        self.repository_stock_quote = repository_stock_quote
        self.repository_indicators = repository_indicators
        self.repository_statements_fetched = repository_statements_fetched
        self.repository_statements_ratio = repository_statements_ratio

        self.uow_factory = uow_factory
        # self.http_client = http_client

        # Initialize the use case responsible for company synchronization
        self.normalize_usecase = NormalizeUseCase(
            config=self.config,
            logger=self.logger,

            repository_company=self.repository_company,
            repository_stock_quote=self.repository_stock_quote,
            repository_indicators=self.repository_indicators,
            repository_statements_fetched=self.repository_statements_fetched,
            repository_statements_ratio=self.repository_statements_ratio,

            uow_factory=self.uow_factory,
            # http_client=self.http_client,

            # max_workers=self.config.worker_pool.max_workers,
        )

    def __call__(self, *args: Any, **kwds: Any) -> SyncResultsDTO:
        return self.run()

    def run(self) -> SyncResultsDTO[StockQuoteDTO]:
        """Trigger company synchronization workflow.

        Returns:
            Any: The result of the synchronization use case execution.
        """
        return self.normalize_usecase()
