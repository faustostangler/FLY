from __future__ import annotations

from application.usecases.search_companies import SearchCompaniesUseCase
from domain.ports.companies_eligible_port import CompaniesEligiblePort
from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging.logger_adapter import Logger
from infrastructure.repositories.repository_company_eligible import (
    RepositoryCompanyEligible,
)
from infrastructure.uow.uow import UowFactory


def get_company_search_usecase() -> SearchCompaniesUseCase:
    config = ConfigAdapter()
    logger = Logger(config)
    repository: CompaniesEligiblePort = RepositoryCompanyEligible(
        config=config,
        logger=logger,
    )
    uow_factory = UowFactory(session_factory=repository.Session)
    return SearchCompaniesUseCase(
        repository=repository,
        uow_factory=uow_factory,
        logger=logger,
    )
