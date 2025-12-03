from application.ports.config_port import ConfigPort
from application.ports.http_client_port import AffinityHttpClientPort
from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from application.ports.worker_pool_port import WorkerPoolPort
from domain.dtos.sync_results_dto import SyncResultsDTO
from domain.polices.nsd_policy import NsdPolicyPort
from domain.ports.cache_ratios_port import CacheRatiosPort
from domain.ports.repository_company_data_port import RepositoryCompanyDataPort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
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
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from domain.services.service_company_data import CompanyDataService
from domain.services.service_nsd import NsdService
from domain.services.service_ratios import RatiosService
from presentation.controllers.filter_presets import (
    build_ratios_filter_by_issuing_company,
)
from domain.services.service_stock_quote import StockQuoteService

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
        repository_stock_quote: RepositoryStockQuotePort,
        repository_indicators: RepositoryIndicatorsPort,
        repository_statements_raw: RepositoryStatementsRawPort,
        repository_statements_fetched: RepositoryStatementFetchedPort,
        cache_ratios: CacheRatiosPort,
        scraper_company_data: ScraperCompanyDataPort,
        scraper_nsd: ScraperNsdPort,
        scraper_statements_raw: ScraperStatementRawPort,
        scraper_stock_quote: ScraperStockQuotePort,
        worker_pool: WorkerPoolPort,
        policy: NsdPolicyPort,
        uow_factory: UowFactoryPort,
        http_client: AffinityHttpClientPort,
        companies_eligible_port: CompaniesEligiblePort,
    ) -> None:
        """Initialize the CLI with injected ports."""
        # Store injected dependencies for later composition
        self.config = config
        self.logger = logger

        self.repository_company = repository_company
        self.repository_nsd = repository_nsd
        self.repository_stock_quote = repository_stock_quote
        self.repository_indicators = repository_indicators
        self.repository_statements_raw = repository_statements_raw
        self.repository_statements_fetched = repository_statements_fetched
        self.cache_ratios = cache_ratios

        self.scraper_company_data = scraper_company_data
        self.scraper_nsd = scraper_nsd
        self.scraper_statements_raw = scraper_statements_raw
        self.scraper_stock_quote = scraper_stock_quote

        self.worker_pool = worker_pool
        self.http_client = http_client

        self.policy = policy
        self.uow_factory = uow_factory

        self.byte_formatter = ByteFormatter()
        self.companies_eligible_port = companies_eligible_port

    def __call__(self) -> None:
        return self.run()

    def run(self) -> None:
        """Execute the top-level application workflow."""
        # Emit lifecycle start event
        self.logger.log("Start FLY", level="info")
        metrics: int = 0

        # # Kick off the company data pipeline
        # company_results: SyncResultsDTO = self._company_service()
        # if company_results:
        #     metrics += company_results.metrics
        #     self.logger.log(f"Company Download: {self.byte_formatter.format_bytes(company_results.metrics)}")

        # # Get NSD and stataments pipeline from B3
        # statements_results: SyncResultsDTO = self._statements_service()
        # if statements_results:
        #     metrics += statements_results.metrics
        #     self.logger.log(f"Statements Download: {self.byte_formatter.format_bytes(statements_results.metrics)}")

        # # Get Stock Value for companies
        # stock_quote_results: SyncResultsDTO = self._stock_quote_service()
        # if stock_quote_results:
        #     metrics += stock_quote_results.metrics
        #     self.logger.log(f"Stock Quotes Download: {self.byte_formatter.format_bytes(stock_quote_results.metrics)}")

        # Ratios Service
        ratios_results: SyncResultsDTO = self._ratios_service()
        if ratios_results:
            metrics += ratios_results.metrics
            self.logger.log(f"Ratios Download: {self.byte_formatter.format_bytes(ratios_results.metrics)}")

        if metrics > 0:
            self.logger.log(f"Total Download: {self.byte_formatter.format_bytes(metrics)}")

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

    def _stock_quote_service(self) -> SyncResultsDTO:
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

    def _ratios_service(self) -> SyncResultsDTO:
        """ """
        ratios_service = RatiosService(
            config=self.config,
            logger=self.logger,

            repository_company=self.repository_company,
            repository_stock_quote=self.repository_stock_quote,
            repository_indicators=self.repository_indicators,
            repository_statements_fetched=self.repository_statements_fetched,
            cache_ratios=self.cache_ratios,

            uow_factory=self.uow_factory,
            worker_pool=self.worker_pool,
            companies_eligible_port=self.companies_eligible_port,
        )

        # run the service
        # filters: Dicionário de filtros (ex: {'company_name': {'contains': 'GERDAU'}}).
        #             Se None, processa todas as empresas elegíveis.
        #             cada folha da árvore é uma condição concreta sobre uma coluna (Cmp, StrMatch, NullCheck, ListAny).
        #             {
        #         "and": [
        #             {"status": "ATIVO"},
        #             {
        #             "or": [
        #                 {
        #                 "and": [
        #                     {"has_bdr": True},
        #                     {"market": {"in": ["NM"]}}
        #                 ]
        #                 },
        #                 {"listing_date": {">=": "2020-01-01"}}
        #             ]
        #             },
        #             {"market": {"in": ["NM", "N2"]}}
        #         ]
        #         }
        #         Essa estrutura representa:
        #         (status == "ATIVO") 
        #         AND ( (has_bdr == True AND market in ["NM"]) OR (listing_date >= "2020-01-01") )
        #         AND (market in ["NM", "N2"])

        filters = build_ratios_filter_by_issuing_company("PETR")

        df_ratios = ratios_service(filters=filters)
        return df_ratios
