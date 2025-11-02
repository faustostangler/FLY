from typing import Any

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from application.services.eligible_companies_batch_updater_service import (
    EligibleCompaniesBatchUpdaterService,
)
from application.usecases.normalize_ratios import NormalizeUseCase
from application.usecases.refresh_eligible_companies_projection import (
    CompaniesEligibleUseCase,
)
from domain.dtos import CacheRatiosResultDTO, SyncResultsDTO
from domain.ports.ratios_cache_port import CacheRatiosPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.companies_eligible_port import CompaniesEligiblePort


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
        cache_ratios: CacheRatiosPort,

        uow_factory: UowFactoryPort,
        worker_pool: WorkerPoolPort,
        companies_eligible_port: CompaniesEligiblePort,
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
        self.cache_ratios = cache_ratios

        self.uow_factory = uow_factory
        self.worker_pool = worker_pool
        # self.http_client = http_client

        self._companies_eligible_batch_service = EligibleCompaniesBatchUpdaterService(
            logger=self.logger,
            port=companies_eligible_port,
        )

        self.companies_eligible_usecase = CompaniesEligibleUseCase(
            logger=self.logger,
            repository_company=self.repository_company,
            repository_statements_fetched=self.repository_statements_fetched,
            repository_stock_quote=self.repository_stock_quote,
            batch_service=self._companies_eligible_batch_service,
            uow_factory=self.uow_factory,
        )

        # Initialize the use case responsible for company synchronization
        self.normalize_usecase = NormalizeUseCase(
            config=self.config,
            logger=self.logger,

            repository_stock_quote=self.repository_stock_quote,
            repository_indicators=self.repository_indicators,
            repository_statements_fetched=self.repository_statements_fetched,
            cache_ratios=self.cache_ratios,
            companies_eligible_port=companies_eligible_port,

            uow_factory=self.uow_factory,
            worker_pool=self.worker_pool,
            # http_client=self.http_client,

            # max_workers=self.config.worker_pool.max_workers,
        )

    def __call__(self, *args: Any, **kwds: Any) -> SyncResultsDTO[CacheRatiosResultDTO]:
        return self.run()

    def run(self) -> SyncResultsDTO[CacheRatiosResultDTO]:
        """Trigger company synchronization workflow.

        Returns:
            Any: The result of the synchronization use case execution.
        """
        self.companies_eligible_usecase()
        return self.normalize_usecase()
