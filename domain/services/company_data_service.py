from application.usecases import SyncCompanyDataUseCase
from domain.ports.repository_company_data_port import CompanyDataRepositoryPort
from domain.ports.scraper_company_data_port import CompanyDataScraperPort
from domain.ports.config_port import ConfigPort
from domain.ports.logger_port import LoggerPort


class CompanyDataService:
    """Service layer to coordinate company-related synchronization use cases."""

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        repository: CompanyDataRepositoryPort,
        scraper: CompanyDataScraperPort,
    ):
        """Initialize the service with required dependencies.

        Args:
            config (ConfigPort): Provides application configuration settings.
            logger (LoggerPort): Logging interface for tracking operations.
            repository (CompanyDataRepositoryPort): Repository for persisting company data.
            scraper (CompanyDataScraperPort): Scraper for fetching company data.
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

    def sync_companies(self) -> None:
        """Trigger company synchronization workflow.

        Returns:
            Any: The result of the synchronization use case execution.
        """
        # Delegate execution to the underlying use case
        result = self.sync_companies_usecase.synchronize_companies()
        return result
