"""Command line interface that wires together the application services."""

from application import CompanyDataMapper
from application.processors.fetch_statements_processor import FetchStatementsProcessor
from application.processors.parse_statements_processor import ParseStatementsProcessor
from application.processors.transform_statements_processor import (
    TransformStatementsProcessor,
)
from application.services.company_data_service import CompanyDataService
from application.services.nsd_service import NsdService
from domain.ports import ConfigPort, LoggerPort
from infrastructure.helpers import WorkerPool
from infrastructure.helpers.metrics_collector import MetricsCollector
from infrastructure.http.circuit_breaker import BreakerPolicy, CircuitBreakerScraper
from infrastructure.http.rate_limiter import RateLimitedScraper, TokenBucket
from infrastructure.http.session_pool import SessionPool
from infrastructure.repositories import (
    SqlAlchemyRepositoryCompanyData,
    SqlAlchemyNsdRepository,
    SqlAlchemyStatementFetchedRepository,
    SqlAlchemyStatementRawRepository,
)
from infrastructure.scrapers import (
    CompanyDataScraper,
    NsdScraper,
    RequestsStatementsRawcraper,
)


class CLIAdapter:
    """Orchestrate FLY application flows via the command line."""

    def __init__(self, config: ConfigPort, logger: LoggerPort, datacleaner) -> None:
        self.config = config
        self.logger = logger
        self.datacleaner = datacleaner
        self.collector = MetricsCollector()
        self.worker_pool_executor = WorkerPool(
            self.config,
            metrics_collector=self.collector,
            max_workers=self.config.global_settings.max_workers or 1,
        )
        self.company_repo = SqlAlchemyRepositoryCompanyData(
            connection_string=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )
        self.session_pool = SessionPool(
            self.config, self.logger, size=self.config.http.session_pool_size
        )
        base_scraper = RequestsStatementsRawcraper(
            pool=self.session_pool,
            timeout=(
                self.config.http.timeout_connect,
                self.config.http.timeout_read,
            ),
            logger=self.logger,
            metrics=self.collector,
        )
        bucket = TokenBucket(
            rate_per_sec=self.config.http.rate_per_sec,
            burst=self.config.http.burst,
        )
        limited = RateLimitedScraper(base_scraper, bucket, self.logger)
        breaker = CircuitBreakerScraper(
            limited,
            self.logger,
            policy=BreakerPolicy(
                failure_threshold=self.config.http.circuit_failures,
                open_seconds=self.config.http.circuit_open_seconds,
            ),
        )
        self.scraper = breaker

    def start_fly(self) -> None:
        """Trigger all main processing pipelines for the FLY system."""
        # self._company_service()
        # self._nsd_service()
        self._statement_service()

    def _company_service(self) -> None:
        """Build and execute the company data synchronization flow."""
        mapper = CompanyDataMapper(self.datacleaner)
        company_repo = self.company_repo
        scraper_company_data = CompanyDataScraper(
            config=self.config,
            logger=self.logger,
            datacleaner=self.datacleaner,
            mapper=mapper,
            worker_pool_executor=self.worker_pool_executor,
            metrics_collector=self.collector,
        )
        company_service = CompanyDataService(
            config=self.config,
            logger=self.logger,
            repository=company_repo,
            scraper=scraper_company_data,
        )
        company_service.sync_companies()

    def _nsd_service(self) -> None:
        """Build and execute the NSD data synchronization flow."""
        company_repo = self.company_repo
        nsd_repo = SqlAlchemyNsdRepository(
            connection_string=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )
        scraper_nsd = NsdScraper(
            config=self.config,
            logger=self.logger,
            datacleaner=self.datacleaner,
            repository=nsd_repo,
            worker_pool_executor=self.worker_pool_executor,
            metrics_collector=self.collector,
        )
        nsd_service = NsdService(
            config=self.config,
            logger=self.logger,
            repository=nsd_repo,
            company_repo=company_repo,
            scraper=scraper_nsd,
        )

        nsd_service.sync_nsd()

    def _statement_service(self) -> None:
        """Build and execute the financial statement pipeline."""
        company_repo = self.company_repo
        nsd_repo = SqlAlchemyNsdRepository(
            connection_string=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )
        raw_statement_repo = SqlAlchemyStatementRawRepository(
            connection_string=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )
        fetched_statement_repo = SqlAlchemyStatementFetchedRepository(
            connection_string=self.config.database.connection_string,
            config=self.config,
            logger=self.logger,
        )

        fetch_processor = FetchStatementsProcessor(
            logger=self.logger,
            config=self.config,
            source=self.scraper,
            company_repo=company_repo,
            nsd_repo=nsd_repo,
            raw_statement_repo=raw_statement_repo,
            fetched_statements_repo=fetched_statement_repo,
            metrics_collector=self.collector,
            worker_pool_executor=self.worker_pool_executor,
        )
        raw_rows = fetch_processor.run()

        parse_pool = WorkerPool(
            config=self.config,
            metrics_collector=self.collector,
            max_workers=self.config.global_settings.max_workers,
        )

        parse_processor = ParseStatementsProcessor(
            logger=self.logger,
            repository=fetched_statement_repo,
            config=self.config,
            worker_pool_executor=parse_pool,
            metrics_collector=self.collector,
            max_workers=self.config.global_settings.max_workers or 1,
        )

        fetched_groups = parse_processor.run(raw_rows)

        transform_processor = TransformStatementsProcessor(
            config=self.config,
            logger=self.logger,
            fetched_repo=fetched_statement_repo,
        )
        transform_processor.run(fetched_groups)
