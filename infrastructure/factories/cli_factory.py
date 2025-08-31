from __future__ import annotations

from application.mappers.company_data_mapper import CompanyDataMapper
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
# from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
# from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from infrastructure.factories.datacleaner_factory import datacleaner_factory
from infrastructure.http.http_client import RequestsAffinityHttpClient
from infrastructure.repositories.repository_company_data import RepositoryCompanyData
from infrastructure.repositories.repository_nsd import RepositoryNsd
from infrastructure.repositories.repository_statements_raw import StatementRawRepository
from infrastructure.repositories.repository_statements_fetched import StatementFetchedRepository
from infrastructure.scrapers.company_data_scraper import CompanyDataScraper
from infrastructure.scrapers.nsd_scraper import NsdScraper
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
    fetched_statements_repository = StatementFetchedRepository(config=config, logger=logger)

    # Compose the data-cleaning pipeline used before mapping/persisting
    datacleaner = datacleaner_factory(config, logger)
    # Create a mapper that converts raw payloads into domain objects
    mapper = CompanyDataMapper(datacleaner)
    # Initialize metrics collection for operational observability
    metrics_collector = MetricsCollector()
    # Provision a worker pool sized by configuration for concurrent tasks
    worker_pool = WorkerPool(config, metrics_collector, config.worker_pool.max_workers)
    # Instantiate the HTTP client with request affinity/session handling
    http_client = RequestsAffinityHttpClient()

    # Assemble the scraper with all required cross-cutting dependencies
    company_scraper = CompanyDataScraper(
        config=config,
        logger=logger,
        datacleaner=datacleaner,
        mapper=mapper,
        metrics_collector=metrics_collector,
        worker_pool=worker_pool,
        http_client=http_client,
    )

    nsd_scraper = NsdScraper(
        config=config,
        logger=logger,
        datacleaner=datacleaner,
        metrics_collector=metrics_collector,
        worker_pool=worker_pool,
        nsd_repository=nsd_repository,
        http_client=http_client,
    )

    # Return the CLI controller with its dependencies injected
    return Cli(
        config=config,
        logger=logger,
        company_repository=company_repository,
        nsd_repository=nsd_repository,
        statements_raw_repository=raw_statements_repository,
        statements_fetched_repository=fetched_statements_repository,

        company_scraper=company_scraper,
        nsd_scraper=nsd_scraper,
    )
