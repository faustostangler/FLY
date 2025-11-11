from __future__ import annotations

from fastapi import Depends

from application.usecases.get_company_accounts_chart import GetCompanyAccountsChartUseCase
from application.usecases.get_company_ratios_frame import GetCompanyRatiosFrameUseCase
from domain.ports.cache_ratios_port import CacheRatiosPort
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from domain.ports.repository_indicators_port import RepositoryIndicatorsPort
from domain.ports.repository_statements_fetched_port import (
    RepositoryStatementFetchedPort,
)
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from infrastructure.cache.ratios_cache import CacheRatiosAdapter
from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging.logger_adapter import Logger
from infrastructure.repositories.repository_company_eligible import (
    RepositoryCompanyEligible,
)
from infrastructure.repositories.repository_indicators import RepositoryIndicators
from infrastructure.repositories.repository_statements_fetched import (
    RepositoryStatementsFetched,
)
from infrastructure.repositories.repository_stock_quote import RepositoryStockQuote
from infrastructure.uow.uow import UowFactory


def get_company_ratios_frame_usecase() -> GetCompanyRatiosFrameUseCase:
    config = ConfigAdapter()
    logger = Logger(config)

    companies_eligible: CompaniesEligiblePort = RepositoryCompanyEligible(
        config=config,
        logger=logger,
    )
    repository_indicators: RepositoryIndicatorsPort = RepositoryIndicators(
        config=config,
        logger=logger,
    )
    repository_statements: RepositoryStatementFetchedPort = RepositoryStatementsFetched(
        config=config,
        logger=logger,
    )
    repository_stock_quote: RepositoryStockQuotePort = RepositoryStockQuote(
        config=config,
        logger=logger,
    )
    cache_ratios: CacheRatiosPort = CacheRatiosAdapter(
        config=config,
        logger=logger,
    )

    uow_factory = UowFactory(session_factory=companies_eligible.Session)

    return GetCompanyRatiosFrameUseCase(
        config=config,
        logger=logger,
        repository_stock_quote=repository_stock_quote,
        repository_indicators=repository_indicators,
        repository_statements_fetched=repository_statements,
        cache_ratios=cache_ratios,
        companies_eligible_port=companies_eligible,
        uow_factory=uow_factory,
    )


def get_company_accounts_chart_usecase(
    ratios_frame_usecase: GetCompanyRatiosFrameUseCase = Depends(get_company_ratios_frame_usecase),
) -> GetCompanyAccountsChartUseCase:
    return GetCompanyAccountsChartUseCase(ratios_frame_usecase=ratios_frame_usecase)
