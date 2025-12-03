# presentation/backend/dependencies.py
from __future__ import annotations

from application.ports.config_port import ConfigPort
from application.ports.uow_port import UowFactoryPort
from application.usecases.get_stock_quote_series import GetStockQuoteSeriesUseCase
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging.logger_adapter import Logger
from infrastructure.repositories.repository_stock_quote import RepositoryStockQuote
from infrastructure.uow.uow import UowFactory


def get_stock_quote_usecase() -> GetStockQuoteSeriesUseCase:
    config = ConfigAdapter()
    logger = Logger(config)
    repository = RepositoryStockQuote(config=config, logger=logger)
    uow_factory = UowFactory(session_factory=repository.Session)
    return GetStockQuoteSeriesUseCase(repository=repository, uow_factory=uow_factory)
