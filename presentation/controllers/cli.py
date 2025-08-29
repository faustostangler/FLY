from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.ports.config_port import ConfigPort
from domain.ports.logger_port import LoggerPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from domain.ports.scraper_company_data_port import ScraperCompanyDataPort
from domain.ports.scraper_nsd_port import ScraperNsdPort
from domain.services.service_company_data import CompanyDataService
from domain.services.service_nsd import NsdService
from infrastructure.utils.byte_formatter import ByteFormatter

class Cli:
    """CLI façade that coordinates domain services.

    This class is intentionally minimal: it composes dependencies and
    triggers the high-level workflows without embedding domain logic.

    Args:
        config (ConfigPort): Read-only application configuration.
        logger (LoggerPort): Logging abstraction for structured events.
        company_repository (RepositoryCompanyDataPort): Persistence port for company data.
        company_scraper (ScraperCompanyDataPort): Scraper port for fetching company data.
    """

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        company_repository: RepositoryCompanyDataPort,
        nsd_repository: RepositoryNsdPort,
        statements_raw_repository: RepositoryStatementsRawPort,
        statements_fetched_repository: RepositoryStatementFetchedPort,
        company_scraper: ScraperCompanyDataPort,
        nsd_scraper: ScraperNsdPort,
    ) -> None:
        """Initialize the CLI with injected ports."""
        # Store injected dependencies for later composition
        self.config = config
        self.logger = logger
        self.company_repository = company_repository
        self.nsd_repository = nsd_repository
        self.statements_raw_repository = statements_raw_repository
        self.statements_fetched_repository = statements_fetched_repository

        self.company_scraper = company_scraper
        self.nsd_scraper = nsd_scraper
        self.byte_formatter = ByteFormatter()

    def run(self) -> None:
        """Execute the top-level application workflow."""
        # Emit lifecycle start event
        self.logger.log("Start FLY", level="info")

        # Kick off the company data pipeline
        # company_results: SyncResultsDTO = self._company_service()
        # self.logger.log(f"Total Download: {self.byte_formatter.format_bytes(company_results.metrics)}")
        self._statements_service()
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

    def _statements_service(self) -> None:
        """Build and execute the NSD synchronization flow."""
        nsd_service = NsdService(
            config=self.config,
            logger=self.logger,
            nsd_repository=self.nsd_repository,
            company_repository=self.company_repository,
            scraper=self.nsd_scraper,
        )

        # Run the synchronization step
        nsd_service.sync_nsd()
