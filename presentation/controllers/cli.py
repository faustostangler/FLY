from typing import List, Tuple

from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.ports import (
    CompanyDataRepositoryPort,
    CompanyDataScraperPort,
    ConfigPort,
    LoggerPort,
)
from domain.services import CompanyDataService


class Cli:
    """CLI façade that coordinates domain services.

    This class is intentionally minimal: it composes dependencies and
    triggers the high-level workflows without embedding domain logic.

    Args:
        config (ConfigPort): Read-only application configuration.
        logger (LoggerPort): Logging abstraction for structured events.
        company_repository (CompanyDataRepositoryPort): Persistence port for company data.
        company_scraper (CompanyDataScraperPort): Scraper port for fetching company data.
    """

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        company_repository: CompanyDataRepositoryPort,
        company_scraper: CompanyDataScraperPort,
    ) -> None:
        """Initialize the CLI with injected ports."""
        # Store injected dependencies for later composition
        self.config = config
        self.logger = logger
        self.company_repository = company_repository
        self.company_scraper = company_scraper

    def run(self) -> None:
        """Execute the top-level application workflow."""
        # Emit lifecycle start event
        self.logger.log("Start FLY", level="info")

        # Kick off the company data pipeline
        self._company_service()

        return None

    def _company_service(self) -> SyncResultsDTO:
        """Build and execute the company data synchronization flow."""
        # Alias injected dependencies for readability
        company_repository = self.company_repository
        company_scraper = self.company_scraper

        # Compose the service with explicit dependencies
        company_service = CompanyDataService(
            config=self.config,
            logger=self.logger,
            repository=company_repository,
            scraper=company_scraper,
        )

        # Run the synchronization step
        return company_service.sync_companies()
