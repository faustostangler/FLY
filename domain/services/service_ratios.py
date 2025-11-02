from typing import Any

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.services.valid_companies_batch_updater_service import (
    ValidCompaniesBatchUpdaterService,
)
from application.usecases.normalize_ratios import NormalizeUseCase
from application.usecases.update_valid_companies_projection import (
    UpdateValidCompaniesProjectionUseCase,
)
from domain.dtos import RatiosCacheResultDTO, SyncResultsDTO
from domain.ports.ratios_cache_port import RatiosCachePort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.valid_companies_read_port import ValidCompaniesReadPort
from domain.ports.valid_companies_write_port import ValidCompaniesWritePort


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
        ratios_cache: RatiosCachePort,

        uow_factory: UowFactoryPort,
        worker_pool: WorkerPoolPort,
        valid_companies_read_port: ValidCompaniesReadPort,
        valid_companies_write_port: ValidCompaniesWritePort,
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
        self.ratios_cache = ratios_cache

        self.uow_factory = uow_factory
        self.worker_pool = worker_pool
        # self.http_client = http_client

        self._valid_companies_batch_service = ValidCompaniesBatchUpdaterService(
            logger=self.logger,
            write_port=valid_companies_write_port,
        )

        self._valid_companies_update_usecase = UpdateValidCompaniesProjectionUseCase(
            logger=self.logger,
            repository_company=self.repository_company,
            repository_statements_fetched=self.repository_statements_fetched,
            repository_stock_quote=self.repository_stock_quote,
            batch_service=self._valid_companies_batch_service,
            uow_factory=self.uow_factory,
        )

        # Initialize the use case responsible for company synchronization
        self.normalize_usecase = NormalizeUseCase(
            config=self.config,
            logger=self.logger,

            repository_stock_quote=self.repository_stock_quote,
            repository_indicators=self.repository_indicators,
            repository_statements_fetched=self.repository_statements_fetched,
            ratios_cache=self.ratios_cache,
            valid_companies_read_port=valid_companies_read_port,

            uow_factory=self.uow_factory,
            worker_pool=self.worker_pool,
            # http_client=self.http_client,

            # max_workers=self.config.worker_pool.max_workers,
        )

    def __call__(self, *args: Any, **kwds: Any) -> SyncResultsDTO[RatiosCacheResultDTO]:
        return self.run()

    def run(self) -> SyncResultsDTO[RatiosCacheResultDTO]:
        """Trigger company synchronization workflow.

        Returns:
            Any: The result of the synchronization use case execution.
        """
        self._valid_companies_update_usecase()
        return self.normalize_usecase()
