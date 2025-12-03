from __future__ import annotations

from application.mappers.company_data_mapper import CompanyDataMapper
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.polices.nsd_policy import NsdPolicy

# from domain.ports.repository_statements_fetched_port import RepositoryStatementFetchedPort
# from domain.ports.repository_statements_raw_port import RepositoryStatementsRawPort
from infrastructure.cache import CacheRatiosAdapter
from infrastructure.factories.datacleaner_factory import datacleaner_factory

# from infrastructure.http.affinity_http_client import RequestsAffinityHttpClient
from infrastructure.http.builders import build_http_client
from infrastructure.repositories.repository_company_data import RepositoryCompanyData
from infrastructure.repositories.repository_indicators import RepositoryIndicators
from infrastructure.repositories.repository_nsd import RepositoryNsd
from infrastructure.repositories.repository_statements_fetched import (
    StatementFetchedRepository,
)
from infrastructure.repositories.repository_statements_raw import StatementRawRepository
from infrastructure.repositories.repository_stock_quote import RepositoryStockQuote
from infrastructure.repositories.repository_company_eligible import (
    RepositoryCompanyEligible,
)
from infrastructure.scrapers.scraper_company_data import CompanyDataScraper
from infrastructure.scrapers.scraper_nsd import NsdScraper
from infrastructure.scrapers.scraper_statements_raw import ScraperStatementRaw
from infrastructure.scrapers.scraper_stock_quote import StockQuoteScraper
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
    repository_company = RepositoryCompanyData(config=config, logger=logger)
    repository_nsd = RepositoryNsd(config=config, logger=logger)
    repository_raw_statements = StatementRawRepository(config=config, logger=logger)
    repository_fetched_statements = StatementFetchedRepository(config=config, logger=logger)
    companies_eligible = RepositoryCompanyEligible(
        config=config,
        logger=logger,
    )
    # companies_eligible_.initialize()
    repository_stock_quote = RepositoryStockQuote(config=config, logger=logger)
    repository_indicators = RepositoryIndicators(config=config, logger=logger)
    cache_ratios = CacheRatiosAdapter(config=config, logger=logger)

    # Unit of Work
    uow_factory = UowFactory(session_factory=repository_nsd.Session)


    # Compose the data-cleaning pipeline used before mapping/persisting
    datacleaner = datacleaner_factory(config, logger)
    # Create a mapper that converts raw payloads into domain objects
    mapper = CompanyDataMapper(datacleaner)
    # Initialize metrics collection for operational observability
    metrics_collector = MetricsCollector()
    # Instantiate the HTTP client with request affinity/session handling
    http_client = build_http_client(config, logger, metrics_collector)
    # Provision a worker pool sized by configuration for concurrent tasks
    worker_pool = WorkerPool(config, metrics_collector, config.worker_pool.max_workers)

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
        repository_nsd=repository_nsd,
        datacleaner=datacleaner,
        metrics_collector=metrics_collector,
        worker_pool=worker_pool,
        http_client=http_client,
    )

    scraper_statements_raw = ScraperStatementRaw(
        config=config,
        logger=logger,
        metrics_collector=metrics_collector,
        # repository_statements_raw=repository_raw_statements,
        # datacleaner=datacleaner,
        # metrics_collector=metrics_collector,
        # worker_pool=worker_pool,
        http_client=http_client,
    )

    scraper_stock_quote = StockQuoteScraper(
        config=config,
        logger=logger,
        repository_stock_quote=repository_stock_quote,
        metrics_collector=metrics_collector,
        worker_pool=worker_pool,
        http_client=http_client,
        uow_factory=uow_factory,
        )

    # Policy
    policy = NsdPolicy(
        allowed_types=tuple(config.domain.statements_types),
        recency_year=config.domain.recency_year,
    )

    # Return the CLI controller with its dependencies injected
    cli = Cli(
        config=config,
        logger=logger,
        repository_company=repository_company,
        repository_nsd=repository_nsd,
        repository_stock_quote=repository_stock_quote,
        repository_indicators=repository_indicators,
        repository_statements_raw=repository_raw_statements,
        repository_statements_fetched=repository_fetched_statements,
        cache_ratios=cache_ratios,
        scraper_company_data=scraper_company_data,
        scraper_nsd=scraper_nsd,
        scraper_statements_raw=scraper_statements_raw,
        scraper_stock_quote=scraper_stock_quote,
        worker_pool=worker_pool,
        policy=policy,
        uow_factory=uow_factory,
        http_client=http_client,
        companies_eligible_port=companies_eligible,
    )

    return cli
