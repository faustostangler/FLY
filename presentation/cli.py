"""Command line interface that wires together the application services."""

from application import CompanyDataMapper
from application.services.company_data_service import CompanyDataService
from application.services.nsd_service import NsdService
from application.services.statement_fetch_service import StatementFetchService
from application.services.statement_transform_service import StatementTransformService

# from application.services.statement_parse_service import StatementParseService
from domain.ports import LoggerPort
from infrastructure.config import Config
from infrastructure.helpers import WorkerPool
from infrastructure.helpers.metrics_collector import MetricsCollector
from infrastructure.repositories import (
    SqlAlchemyCompanyDataRepository,
    SqlAlchemyNsdRepository,
    SqlAlchemyParsedStatementRepository,
    SqlAlchemyRawStatementRepository,
)
from infrastructure.scrapers.company_data_exchange_scraper import CompanyDataScraper
from infrastructure.scrapers.nsd_scraper import NsdScraper
from infrastructure.scrapers.requests_raw_statement_scraper import (
    RawStatementScraper,
)


class CLIAdapter:
    """Primary CLI controller responsible for orchestrating FLY application
    flows."""

    def __init__(self, config: Config, logger: LoggerPort, data_cleaner):
        """Initialize CLIAdapter and its supporting infrastructure.

        Args:
            config (Config): Loaded application configuration.
            logger (LoggerPort): Application logger for emitting progress and diagnostics.
            data_cleaner: Utility responsible for data sanitation during scraping.
        """
        # Store configuration object for downstream components
        self.config = config

        # Store logger for CLI progress messages and service logs
        self.logger = logger

        # Provide cleaning logic for raw scraped inputs
        self.data_cleaner = data_cleaner

        # Initialize collector for execution metrics (used by scrapers)
        # self.logger.log("Instantiate collector", level="info")
        self.collector = MetricsCollector()
        # self.logger.log("End Instance collector", level="info")

        # Build worker pool for concurrent task execution
        # self.logger.log("Instantiate worker_pool_executor", level="info")
        self.worker_pool_executor = WorkerPool(
            self.config,
            metrics_collector=self.collector,
            max_workers=self.config.global_settings.max_workers or 1,
        )
        # self.logger.log("End Instance worker_pool_executor", level="info")

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def start_fly(self) -> None:
        """Trigger all main processing pipelines for the FLY system."""
        # self.logger.log("Run  Method controller.run()", level="info")

        # Run company scraper and persist logic
        # self.logger.log("Call Method controller.run()._company_service()", level="info")
        # self._company_service()
        # self.logger.log("End  Method controller.run()._company_service()", level="info")

        # Run NSD fetcher and synchronization
        # self.logger.log("Call Method controller.run()._nsd_service()", level="info")
        # self._nsd_service()
        # self.logger.log("End  Method controller.run()._nsd_service()", level="info")

        # Fetch and optionally parse statements
        # self.logger.log("Call Method controller.run()._statement_service()", level="info")
        self._statement_service()
        # self.logger.log("End  Method controller.run()._statement_service()", level="info")

        # self.logger.log("End  Method controller.run()", level="info")

    def _company_service(self) -> None:
        """Build and execute the company data synchronization flow."""
        # self.logger.log("Run  Method controller.run()._company_service()", level="info")

        # Initialize data mapper for company DTO transformation
        # self.logger.log("Instantiate mapper", level="info")
        mapper = CompanyDataMapper(self.data_cleaner)
        # self.logger.log("End Instance mapper", level="info")

        # Set up persistent repository for companies
        # self.logger.log("Instantiate company_repo", level="info")
        company_repo = SqlAlchemyCompanyDataRepository(
            config=self.config, logger=self.logger
        )
        # self.logger.log("End Instance company_repo", level="info")

        # Create scraping engine for company data
        # self.logger.log("Instantiate company_scraper (mapper, worker_pool_executor, collector)", level="info")
        company_scraper = CompanyDataScraper(
            config=self.config,
            logger=self.logger,
            data_cleaner=self.data_cleaner,
            mapper=mapper,
            worker_pool_executor=self.worker_pool_executor,
            metrics_collector=self.collector,
        )
        # self.logger.log("End Instance company_scraper (mapper, worker_pool_executor, collector)", level="info")

        # Combine repository and scraper in the application service
        # self.logger.log("Instantiate company_service (company_repo, scraper)", level="info")
        company_service = CompanyDataService(
            config=self.config,
            logger=self.logger,
            repository=company_repo,
            scraper=company_scraper,
        )

        # Trigger data sync workflow
        # self.logger.log("Call Method controller.start().company_service.sync_companies()", level="info")
        company_service.sync_companies()
        # self.logger.log("Finish Method controller.start().company_service.sync_companies()", level="info")

        # self.logger.log("End Instance company_service (company_repo, scraper)", level="info")

    def _nsd_service(self) -> None:
        """Build and execute the NSD data synchronization flow."""
        # self.logger.log("Run  Method controller.run()._nsd_service()", level="info")

        # Create repository for storing NSD records
        # self.logger.log("Instantiate nsd_repo", level="info")
        nsd_repo = SqlAlchemyNsdRepository(config=self.config, logger=self.logger)
        # self.logger.log("End Instance nsd_repo", level="info")

        # Build NSD scraper with concurrent capabilities
        # self.logger.log("Instantiate nsd_scraper (worker_pool_executor, collector, nsd_repo)", level="info")
        nsd_scraper = NsdScraper(
            config=self.config,
            logger=self.logger,
            data_cleaner=self.data_cleaner,
            repository=nsd_repo,
            worker_pool_executor=self.worker_pool_executor,
            metrics_collector=self.collector,
        )
        # self.logger.log("End Instance nsd_scraper (worker_pool_executor, collector, nsd_repo)", level="info")

        # Wrap repository and scraper into a cohesive application service
        # self.logger.log("Instantiate nsd_service (nsd_repo, nsd_scraper)", level="info")
        nsd_service = NsdService(
            logger=self.logger,
            repository=nsd_repo,
            scraper=nsd_scraper,
        )

        # Run the NSD synchronization process
        # self.logger.log("Call Method controller.start()._nsd_service().sync_nsd()", level="info")
        nsd_service.sync_nsd()
        # self.logger.log("End  Method controller.start()._nsd_service().sync_nsd()", level="info")

        # self.logger.log("End Instance nsd_service (nsd_repo, nsd_scraper)", level="info")

    def _statement_service(self) -> None:
        """Build and execute the financial statement fetch flow."""
        # self.logger.log("Run  Method controller.run()._statement_service()", level="info")

        # Initialize all required repositories
        # self.logger.log("Instantiate company_repo", level="info")
        company_repo = SqlAlchemyCompanyDataRepository(
            config=self.config, logger=self.logger
        )
        # self.logger.log("End Instance company_repo", level="info")

        # self.logger.log("Instantiate nsd_repo", level="info")
        nsd_repo = SqlAlchemyNsdRepository(config=self.config, logger=self.logger)
        # self.logger.log("End Instance nsd_repo", level="info")

        # self.logger.log("Instantiate raw_statement_repo", level="info")
        raw_statement_repo = SqlAlchemyRawStatementRepository(
            config=self.config, logger=self.logger
        )
        # self.logger.log("End Instance raw_statement_repo", level="info")

        # self.logger.log("Instantiate parsed_statements_repo", level="info")
        parsed_statement_repo = SqlAlchemyParsedStatementRepository(
            config=self.config, logger=self.logger
        )
        # self.logger.log("End Instance parsed_statements_repo", level="info")

        # Set up the raw statements scraper (adapter)
        # self.logger.log("Instantiate source", level="info")
        raw_statements_scraper = RawStatementScraper(
            config=self.config,
            logger=self.logger,
            data_cleaner=self.data_cleaner,
            metrics_collector=self.collector,
            worker_pool_executor=self.worker_pool_executor,
        )
        # self.logger.log("End Instance source", level="info")

        # Compose fetch service with all dependencies
        # self.logger.log("Instantiate statements_fetch_service (...)", level="info")
        _statements_fetch_service = StatementFetchService(
            logger=self.logger,
            config=self.config,
            source=raw_statements_scraper,
            company_repo=company_repo,
            nsd_repo=nsd_repo,
            raw_statement_repo=raw_statement_repo,
            parsed_statements_repo=parsed_statement_repo,
            metrics_collector=self.collector,
            worker_pool_executor=self.worker_pool_executor,
        )

        # Execute fetch process and log total rows fetched
        # self.logger.log("Call Method controller.run()._statement_service().statements_fetch_service.run()", level="info")
        # raw_rows = statements_fetch_service.fetch_statements()

        # self.logger.log(f"total {len(raw_rows)}")

        # all_rows = []
        # for _nsd, rows in raw_rows:
        #     all_rows.extend(rows)

        transform_service = StatementTransformService(
            logger=self.logger,
            raw_repo=raw_statement_repo,
            parsed_repo=parsed_statement_repo,
            config=self.config,
        )
        transform_service.transform_all()
# =======
#         company_keys = raw_statement_repo.get_existing_by_columns("company_name")

#         for (company_name,) in company_keys:
#             self.logger.log(f"[{company_name}] Starting transformation", level="info")


#         parsed = usecase.execute(raw_dtos)
#         parsed_statement_repo.save_all(parsed)
# >>>>>>> 2025-07-16-Statements-Round-2
