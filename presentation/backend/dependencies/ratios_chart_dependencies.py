from __future__ import annotations

from fastapi import Depends

from application.usecases.get_company_accounts_chart import (
    GetCompanyAccountsChartUseCase,
)
from application.usecases.get_company_ratios_frame import GetCompanyRatiosFrameUseCase
from infrastructure.cache.ratios_cache import CacheRatiosAdapter
from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging.logger_adapter import Logger
from infrastructure.repositories.repository_company_eligible import (
    RepositoryCompanyEligible,
)
from infrastructure.repositories.repository_indicators import RepositoryIndicators
from infrastructure.repositories.repository_statements_fetched import (
    StatementFetchedRepository,
)
from infrastructure.repositories.repository_stock_quote import RepositoryStockQuote
from infrastructure.uow.uow import UowFactory
from infrastructure.utils.metrics_collector import MetricsCollector
from infrastructure.utils.worker_pool import WorkerPool


def get_company_ratios_frame_usecase() -> GetCompanyRatiosFrameUseCase:
    config = ConfigAdapter()
    logger = Logger(config)

    repository_company = RepositoryCompanyEligible(config=config, logger=logger)
    repository_indicators = RepositoryIndicators(config=config, logger=logger)
    repository_statements = StatementFetchedRepository(config=config, logger=logger)
    repository_stock_quote = RepositoryStockQuote(config=config, logger=logger)

    uow_factory = UowFactory(session_factory=repository_company.Session)

    cache_port = CacheRatiosAdapter(config=config, logger=logger)

    metrics = MetricsCollector()
    worker_pool = WorkerPool(config=config, metrics_collector=metrics, max_workers=config.worker_pool.max_workers)

    return GetCompanyRatiosFrameUseCase(
        config=config,
        logger=logger,
        repository_stock_quote=repository_stock_quote,
        repository_indicators=repository_indicators,
        repository_statements_fetched=repository_statements,
        cache_ratios=cache_port,
        companies_eligible_port=repository_company,
        uow_factory=uow_factory,
        worker_pool=worker_pool,
    )


def get_company_accounts_chart_usecase(
    ratios_usecase: GetCompanyRatiosFrameUseCase = Depends(get_company_ratios_frame_usecase),
) -> GetCompanyAccountsChartUseCase:
    return GetCompanyAccountsChartUseCase(ratios_frame_usecase=ratios_usecase)


__all__ = [
    "get_company_accounts_chart_usecase",
    "get_company_ratios_frame_usecase",
]

