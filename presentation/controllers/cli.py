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
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from domain.ports.scraper_company_data_port import ScraperCompanyDataPort
from domain.ports.scraper_nsd_port import ScraperNsdPort
from domain.ports.scraper_statements_raw_port import ScraperStatementRawPort
from domain.ports.scraper_stock_quote_port import ScraperStockQuotePort
from domain.services.financial_normalizer import FinancialNormalizerPort
from domain.services.ratios_calculator import RatiosCalculatorPort
from domain.services.service_company_data import CompanyDataService
from domain.services.service_nsd import NsdService
from domain.services.service_stock_quote import StockQuoteService
from application.ports.http_client_port import AffinityHttpClientPort

# from domain.ports.scraper_statements_fetched_port import ScraperStatementFetchedPort
from infrastructure.utils.byte_formatter import ByteFormatter


class Cli:
    """CLI façade that coordinates domain services.

    This class is intentionally minimal: it composes dependencies and
    triggers the high-level workflows without embedding domain logic.

    Args:
        config (ConfigPort): Read-only application configuration.
        logger (LoggerPort): Logging abstraction for structured events.
        repository_company (RepositoryCompanyDataPort): Persistence port for company data.
        scraper_company_data (ScraperCompanyDataPort): Scraper port for fetching company data.
    """

    def __init__(
        self,
        config: ConfigPort,
        logger: LoggerPort,
        repository_company: RepositoryCompanyDataPort,
        repository_nsd: RepositoryNsdPort,
        repository_statements_raw: RepositoryStatementsRawPort,
        repository_statements_fetched: RepositoryStatementFetchedPort,
        repository_stock_quote: RepositoryStockQuotePort,
        scraper_company_data: ScraperCompanyDataPort,
        scraper_nsd: ScraperNsdPort,
        scraper_statements_raw: ScraperStatementRawPort,
        scraper_stock_quote: ScraperStockQuotePort,
        worker_pool: WorkerPoolPort,
        policy: NsdPolicyPort,
        uow_factory: UowFactoryPort,
        http_client: AffinityHttpClientPort,
        financial_normalizer: FinancialNormalizerPort,
        ratios_calculator: RatiosCalculatorPort,
    ) -> None:
        """Initialize the CLI with injected ports."""
        # Store injected dependencies for later composition
        self.config = config
        self.logger = logger

        self.repository_company = repository_company
        self.repository_nsd = repository_nsd
        self.repository_statements_raw = repository_statements_raw
        self.repository_statements_fetched = repository_statements_fetched
        self.repository_stock_quote = repository_stock_quote

        self.scraper_company_data = scraper_company_data
        self.scraper_nsd = scraper_nsd
        self.scraper_statements_raw = scraper_statements_raw
        self.scraper_stock_quote = scraper_stock_quote

        self.worker_pool = worker_pool
        self.http_client = http_client

        self.policy = policy
        self.uow_factory = uow_factory
        self.financial_normalizer = financial_normalizer
        self.ratios_calculator = ratios_calculator

        self.byte_formatter = ByteFormatter()

    def __call__(self) -> None:
        return self.run()

    def run(self) -> None:
        """Execute the top-level application workflow."""
        # Emit lifecycle start event
        self.logger.log("Start FLY", level="info")

        # Kick off the company data pipeline
        company_results: SyncResultsDTO = self._company_service()
        self.logger.log(
            f"Total Download: {self.byte_formatter.format_bytes(company_results.metrics)}"
        )

        # # Get NSD and stataments pipeline from B3
        # self._statements_service()

        # Get Stock Value for companies
        self.stock_quote_service()

        return None

    def _company_service(self) -> SyncResultsDTO:
        """Build and execute the company data synchronization flow."""
        # Alias injected dependencies for readability
        repository_company = self.repository_company
        scraper_company_data = self.scraper_company_data

        # Compose the service with explicit dependencies
        company_service = CompanyDataService(
            config=self.config,
            logger=self.logger,
            repository_company=repository_company,
            scraper_company_data=scraper_company_data,
            uow_factory=self.uow_factory,
        )

        # Run the synchronization step
        return company_service()

    def _statements_service(self) -> SyncResultsDTO:
        """ """

        nsd_service = NsdService(
            config=self.config,
            logger=self.logger,
            repository_company=self.repository_company,
            repository_nsd=self.repository_nsd,
            repository_statements_raw=self.repository_statements_raw,
            repository_statements_fetched=self.repository_statements_fetched,
            scraper_company_data=self.scraper_company_data,
            scraper_nsd=self.scraper_nsd,
            scraper_statements_raw=self.scraper_statements_raw,
            worker_pool=self.worker_pool,
            policy=self.policy,  # porta para política composta
            financial_normalizer=self.financial_normalizer,  # serviço de domínio puro
            ratios_calculator=self.ratios_calculator,  # serviço de domínio puro
            uow_factory=self.uow_factory,
        )

        # Run the synchronization step
        return nsd_service()

    def stock_quote_service(self) -> SyncResultsDTO:
        """ """
        stock_quote_service = StockQuoteService(
            config=self.config,
            logger=self.logger,
            repository_company=self.repository_company,
            repository_stock_quote=self.repository_stock_quote,
            scraper_stock_quote=self.scraper_stock_quote,
            # worker_pool=self.worker_pool,
            uow_factory=self.uow_factory,
            # http_client=self.http_client,
        )

        # run the service
        return stock_quote_service()
