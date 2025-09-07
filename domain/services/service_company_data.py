from typing import Any
from application.usecases import SyncCompanyDataUseCase
from domain.dtos.sync_results_dto import SyncResultsDTO
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.scraper_company_data_port import ScraperCompanyDataPort


class CompanyDataService:
    """Service layer to coordinate company-related synchronization use cases."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        repository: RepositoryCompanyDataPort,
        scraper: ScraperCompanyDataPort,
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

        # Initialize the use case responsible for company synchronization
        self.sync_companies_usecase = SyncCompanyDataUseCase(
            config=self.config,
            logger=self.logger,
            repository=repository,
            scraper=scraper,
            max_workers=self.config.worker_pool.max_workers,
        )

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        try:
            return self.run()
        except Exception as e:
            pass

    def run(self) -> SyncResultsDTO:
        """Trigger company synchronization workflow.

        Returns:
            Any: The result of the synchronization use case execution.
        """
        # Delegate execution to the underlying use case
        return self.sync_companies_usecase()
