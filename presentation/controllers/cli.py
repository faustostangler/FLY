from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.polices.nsd_policy import NsdPolicyPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_nsd_port import RepositoryNsdPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from domain.ports.scraper_company_data_port import ScraperCompanyDataPort
from domain.ports.scraper_nsd_port import ScraperNsdPort
from domain.ports.scraper_statements_raw_port import ScraperStatementRawPort
from domain.services.financial_normalizer import FinancialNormalizerPort
from domain.services.ratios_calculator import RatiosCalculatorPort
from domain.services.service_company_data import CompanyDataService
from domain.services.service_nsd import NsdService

# from domain.ports.scraper_statements_fetched_port import ScraperStatementFetchedPort
from infrastructure.utils.byte_formatter import ByteFormatter


class Cli:
    """CLI façade that coordinates domain services.

    This class is intentionally minimal: it composes dependencies and
    triggers the high-level workflows without embedding domain logic.

    Args:
        config (ConfigPort): Read-only application configuration.
        logger (LoggerPort): Logging abstraction for structured events.
        company_repository (RepositoryCompanyDataPort): Persistence port for company data.
        scraper_company_data (ScraperCompanyDataPort): Scraper port for fetching company data.
    """

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        company_repository: RepositoryCompanyDataPort,
        nsd_repository: RepositoryNsdPort,
        statements_raw_repository: RepositoryStatementsRawPort,
        statements_fetched_repository: RepositoryStatementFetchedPort,
        scraper_company_data: ScraperCompanyDataPort,
        scraper_nsd: ScraperNsdPort,
        scraper_statements_raw: ScraperStatementRawPort,
        worker_pool: WorkerPoolPort,
        policy: NsdPolicyPort,
        uow_factory: UowFactoryPort,
        financial_normalizer: FinancialNormalizerPort,
        ratios_calculator: RatiosCalculatorPort,
    ) -> None:
        """Initialize the CLI with injected ports."""
        # Store injected dependencies for later composition
        self.config = config
        self.logger = logger

        self.company_repository = company_repository
        self.nsd_repository = nsd_repository
        self.statements_raw_repository = statements_raw_repository
        self.statements_fetched_repository = statements_fetched_repository

        self.scraper_company_data = scraper_company_data
        self.scraper_nsd = scraper_nsd
        self.scraper_statements_raw = scraper_statements_raw

        self.worker_pool = worker_pool

        self.policy = policy
        self.uow_factory = uow_factory
        self.financial_normalizer = financial_normalizer
        self.ratios_calculator = ratios_calculator

        self.byte_formatter = ByteFormatter()

    def __call__(self) -> None:
        try:
            return self.run()
        except Exception:
            pass

    def run(self) -> None:
        """Execute the top-level application workflow."""
        # Emit lifecycle start event
        self.logger.log("Start FLY", level="info")

        # Kick off the company data pipeline
        # company_results: SyncResultsDTO = self._company_service()
        # self.logger.log(
        #     f"Total Download: {self.byte_formatter.format_bytes(company_results.metrics)}"
        # )

        self._statements_service()

        return None

    def _company_service(self) -> SyncResultsDTO:
        """Build and execute the company data synchronization flow."""
        # Alias injected dependencies for readability
        company_repository = self.company_repository
        scraper_company_data = self.scraper_company_data

        # Compose the service with explicit dependencies
        company_service = CompanyDataService(
            config=self.config,
            logger=self.logger,
            repository=company_repository,
            scraper=scraper_company_data,
            uow_factory=self.uow_factory,
        )

        # Run the synchronization step
        return company_service()

    def _statements_service(self) -> SyncResultsDTO:
        """ """

        nsd_service = NsdService(
            config=self.config,
            logger=self.logger,
            company_repository=self.company_repository,
            nsd_repository=self.nsd_repository,
            statements_raw_repository=self.statements_raw_repository,
            statements_fetched_repository=self.statements_fetched_repository,
            scraper_company_data=self.scraper_company_data,
            scraper_nsd=self.scraper_nsd,
            scraper_statements_raw=self.scraper_statements_raw,
            worker_pool=self.worker_pool,
            policy=self.policy,  # porta para política composta
            financial_normalizer=self.financial_normalizer,  # serviço de domínio puro
            ratios_calculator=self.ratios_calculator,  # serviço de domínio puro
            uow_factory=self.uow_factory,  # fábrica de UoW (SQLAlchemy + SQLite)
        )

        # Run the synchronization step
        return nsd_service()
