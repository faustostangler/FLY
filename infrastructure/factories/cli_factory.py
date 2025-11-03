"""Composition root building the CLI controller."""

from __future__ import annotations

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.services.eligible_companies_service import EligibleCompaniesService
from application.usecases.statements_sync import StatementsUseCase
from application.usecases.statements_transformer import StatementTransformer
from domain.services.service_ratios import RatiosService
from infrastructure.cache import CacheRatiosAdapter
from infrastructure.factories.datacleaner_factory import datacleaner_factory
from infrastructure.repositories.eligible_companies_repository import (
    EligibleCompaniesReadRepository,
    EligibleCompaniesWriteRepository,
)
from infrastructure.repositories.repository_company_data import RepositoryCompanyData
from infrastructure.repositories.repository_indicators import RepositoryIndicators
from infrastructure.repositories.repository_statements_fetched import (
    StatementFetchedRepository,
)
from infrastructure.repositories.repository_statements_raw import StatementRawRepository
from infrastructure.repositories.repository_stock_quote import RepositoryStockQuote
from infrastructure.uow.uow import UowFactory
from infrastructure.utils.metrics_collector import MetricsCollector
from infrastructure.utils.worker_pool import WorkerPool
from presentation.controllers.cli import Cli


def cli_factory(config: ConfigPort, logger: LoggerPort) -> Cli:
    """Wire dependencies for the CLI controller."""

    # Persistence adapters -----------------------------------------------------
    repository_company = RepositoryCompanyData(config=config, logger=logger)
    repository_raw_statements = StatementRawRepository(config=config, logger=logger)
    repository_fetched_statements = StatementFetchedRepository(config=config, logger=logger)
    repository_stock_quote = RepositoryStockQuote(config=config, logger=logger)
    repository_indicators = RepositoryIndicators(config=config, logger=logger)
    eligible_read_repository = EligibleCompaniesReadRepository(config=config, logger=logger)
    eligible_write_repository = EligibleCompaniesWriteRepository(config=config, logger=logger)
    cache_ratios = CacheRatiosAdapter(config=config, logger=logger)

    # Unit of work factory shared across services
    uow_factory = UowFactory(session_factory=repository_company.Session)

    # Statement transformation stack ------------------------------------------
    datacleaner = datacleaner_factory(config, logger)
    statement_transformer = StatementTransformer(datacleaner)
    metrics_collector = MetricsCollector()
    worker_pool = WorkerPool(config, metrics_collector, config.worker_pool.max_workers)

    statements_use_case = StatementsUseCase(
        logger=logger,
        repository_statements_raw=repository_raw_statements,
        repository_statements_fetched=repository_fetched_statements,
        transformer=statement_transformer,
        uow_factory=uow_factory,
    )

    eligible_companies_service = EligibleCompaniesService(
        logger=logger,
        repository_company=repository_company,
        repository_statements_fetched=repository_fetched_statements,
        repository_stock_quote=repository_stock_quote,
        read_port=eligible_read_repository,
        write_port=eligible_write_repository,
        uow_factory=uow_factory,
    )

    ratios_service = RatiosService(
        config=config,
        logger=logger,
        repository_stock_quote=repository_stock_quote,
        repository_indicators=repository_indicators,
        repository_statements_fetched=repository_fetched_statements,
        cache_ratios=cache_ratios,
        uow_factory=uow_factory,
        worker_pool=worker_pool,
        eligible_companies_read_port=eligible_read_repository,
    )

    return Cli(
        config=config,
        logger=logger,
        statements_use_case=statements_use_case,
        eligible_companies_service=eligible_companies_service,
        ratios_service=ratios_service,
    )
*** End of File
