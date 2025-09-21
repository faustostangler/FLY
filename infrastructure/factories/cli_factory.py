from __future__ import annotations

from application.mappers.company_data_mapper import CompanyDataMapper
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.polices.nsd_policy import NsdPolicy
from domain.services.financial_normalizer import FinancialNormalizer
from domain.services.ratios_calculator import RatiosCalculator

# from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
# from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from infrastructure.factories.datacleaner_factory import datacleaner_factory
from infrastructure.factories.stock_value_factory import build_stock_value_service

# from infrastructure.http.affinity_http_client import RequestsAffinityHttpClient
from infrastructure.http.builders import build_http_client
from infrastructure.repositories.repository_company_data import RepositoryCompanyData
from infrastructure.repositories.repository_nsd import RepositoryNsd
from infrastructure.repositories.repository_statements_fetched import (
    StatementFetchedRepository,
)
from infrastructure.repositories.repository_statements_raw import StatementRawRepository
from infrastructure.scrapers.scraper_company_data import CompanyDataScraper
from infrastructure.scrapers.scraper_nsd import NsdScraper
from infrastructure.scrapers.scraper_statements_raw import ScraperStatementRaw
from infrastructure.uow.uow import UowFactory
from infrastructure.utils.metrics_collector import MetricsCollector
from infrastructure.utils.worker_pool import WorkerPool
from presentation.controllers.cli import Cli


def cli_factory(config: ConfigPort, logger: LoggerPort) -> Cli:
    """Compose and return the CLI controller with all dependencies wired.

    This factory acts as the composition root for the CLI surface, building
    infrastructure services (repository, HTTP client, worker pool, metrics),
    application services (scraper, mapper, data cleaner), and injecting them
    into the `Cli` controller.

    Args:
        config (ConfigPort): Read-only access to application configuration.
        logger (LoggerPort): Logging facade used by composed components.

    Returns:
        Cli: A fully initialized CLI controller ready for execution.
    """

    # Build the repository backed by the configured persistence layer
    company_repository = RepositoryCompanyData(config=config, logger=logger)
    nsd_repository = RepositoryNsd(config=config, logger=logger)
    raw_statements_repository = StatementRawRepository(config=config, logger=logger)
    fetched_statements_repository = StatementFetchedRepository(
        config=config, logger=logger
    )

    # Unit of Work
    uow_factory = UowFactory(session_factory=nsd_repository.Session)

    # Compose the data-cleaning pipeline used before mapping/persisting
    datacleaner = datacleaner_factory(config, logger)
    # Create a mapper that converts raw payloads into domain objects
    mapper = CompanyDataMapper(datacleaner)
    # Initialize metrics collection for operational observability
    metrics_collector = MetricsCollector()
    # Provision a worker pool sized by configuration for concurrent tasks
    worker_pool = WorkerPool(config, metrics_collector, config.worker_pool.max_workers)
    # Instantiate the HTTP client with request affinity/session handling
    http_client = build_http_client(config, logger)

    # Assemble the scraper with all required cross-cutting dependencies
    scraper_company_data = CompanyDataScraper(
        config=config,
        logger=logger,
        datacleaner=datacleaner,
        mapper=mapper,
        metrics_collector=metrics_collector,
        worker_pool=worker_pool,
        http_client=http_client,
        uow_factory=uow_factory,
    )

    scraper_nsd = NsdScraper(
        config=config,
        logger=logger,
        nsd_repository=nsd_repository,
        datacleaner=datacleaner,
        metrics_collector=metrics_collector,
        worker_pool=worker_pool,
        http_client=http_client,
    )

    scraper_statements_raw = ScraperStatementRaw(
        config=config,
        logger=logger,
        # statements_raw_repository=raw_statements_repository,
        # datacleaner=datacleaner,
        # metrics_collector=metrics_collector,
        # worker_pool=worker_pool,
        http_client=http_client,
    )

    # Policy
    policy = NsdPolicy(
        allowed_types=tuple(config.domain.statements_types),
        recency_year=config.domain.recency_year,
    )

    # Financial Normalizer
    financial_normalizer = FinancialNormalizer()

    # Ratios
    ratios_calculator = RatiosCalculator(
        intel_module_path=(getattr(config.domain, "intel_module_path", None))
    )

    # Stock Value Service
    stock_value_service, stock_value_start = build_stock_value_service(
        config=config, logger=logger
    )

    # Return the CLI controller with its dependencies injected
    cli = Cli(
        config=config,
        logger=logger,
        company_repository=company_repository,
        nsd_repository=nsd_repository,
        statements_raw_repository=raw_statements_repository,
        statements_fetched_repository=fetched_statements_repository,
        scraper_company_data=scraper_company_data,
        scraper_nsd=scraper_nsd,
        scraper_statements_raw=scraper_statements_raw,
        worker_pool=worker_pool,
        policy=policy,
        uow_factory=uow_factory,
        financial_normalizer=financial_normalizer,
        ratios_calculator=ratios_calculator,
        stock_value_service=stock_value_service,
    )

    return cli
