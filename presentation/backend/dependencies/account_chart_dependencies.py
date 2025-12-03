from __future__ import annotations

from application.usecases.get_account_series import GetAccountSeriesUseCase
from domain.ports.repository_account_series_port import RepositoryAccountSeriesPort
from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging.logger_adapter import Logger
from infrastructure.repositories.repository_account_series import RepositoryAccountSeries
from infrastructure.uow.uow import UowFactory


def get_account_series_usecase() -> GetAccountSeriesUseCase:
    config = ConfigAdapter()
    logger = Logger(config)
    repository: RepositoryAccountSeriesPort = RepositoryAccountSeries(
        config=config,
        logger=logger,
    )
    uow_factory = UowFactory(session_factory=repository.Session)
    return GetAccountSeriesUseCase(repository=repository, uow_factory=uow_factory)
