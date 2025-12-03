from __future__ import annotations

from application.usecases.get_company_facets import GetCompanyFacetsUseCase
from domain.ports.repository_company_eligible_port import RepositoryCompanyEligiblePort
from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging.logger_adapter import Logger
from infrastructure.repositories.repository_company_eligible import (
    RepositoryCompanyEligible,
)
from infrastructure.uow.uow import UowFactory


def get_company_facets_usecase() -> GetCompanyFacetsUseCase:
    config = ConfigAdapter()
    logger = Logger(config)
    repository: RepositoryCompanyEligiblePort = RepositoryCompanyEligible(
        config=config,
        logger=logger,
    )
    uow_factory = UowFactory(session_factory=repository.Session)
    return GetCompanyFacetsUseCase(repository=repository, uow_factory=uow_factory)
