# presentation/backend/dependencies.py
from __future__ import annotations

from functools import lru_cache

from application.ports.config_port import ConfigPort
from application.ports.uow_port import UowFactoryPort
from application.usecases.get_stock_quote_series import GetStockQuoteSeriesUseCase
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort
from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging.logger_adapter import Logger
from infrastructure.repositories.repository_stock_quote import RepositoryStockQuote
from infrastructure.uow.uow import UowFactory


@lru_cache
def get_config() -> ConfigPort:
    # Usa PathConfig / load_paths internamente para achar o fly.db
    return ConfigAdapter()


@lru_cache
def get_logger() -> Logger:
    config = get_config()
    return Logger(config)


@lru_cache
def get_stock_quote_repository() -> RepositoryStockQuotePort:
    """
    Adapter concreto de repositório, mas retornado pela interface (Port).
    """
    config = get_config()
    logger = get_logger()
    return RepositoryStockQuote(config=config, logger=logger)


@lru_cache
def get_uow_factory() -> UowFactoryPort:
    """
    UoW baseado na Session do repositório.
    """
    repo = get_stock_quote_repository()
    # RepositoryBase/EngineSetup expõe .Session
    return UowFactory(session_factory=repo.Session)


def get_stock_quote_usecase() -> GetStockQuoteSeriesUseCase:
    """
    Função de dependência para o FastAPI (Depends).

    Exposta como factory na borda de apresentação.
    """
    repository = get_stock_quote_repository()
    uow_factory = get_uow_factory()
    return GetStockQuoteSeriesUseCase(
        repository=repository,
        uow_factory=uow_factory,
    )
