from typing import Any

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.usecases import SyncCompanyDataUseCase
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.scraper_company_data_port import ScraperCompanyDataPort


class CompanyDataService:
    """Service layer to coordinate company-related synchronization use cases."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,

        repository_company: RepositoryCompanyDataPort,
        scraper_company_data: ScraperCompanyDataPort,

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
        self.scraper_company_data = scraper_company_data

        self.uow_factory = uow_factory

        # Initialize the use case responsible for company synchronization
        self.sync_companies_usecase = SyncCompanyDataUseCase(
            config=self.config,
            logger=self.logger,

            repository_company=self.repository_company,
            scraper_company_data=self.scraper_company_data,

            uow_factory=self.uow_factory,

            max_workers=self.config.worker_pool.max_workers,
        )

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.run()

    def run(self) -> SyncResultsDTO:
        """Trigger company synchronization workflow.

        Returns:
            Any: The result of the synchronization use case execution.
        """
        # Delegate execution to the underlying use case
        return self.sync_companies_usecase()
