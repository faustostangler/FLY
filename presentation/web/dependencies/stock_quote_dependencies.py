from functools import lru_cache

from application.usecases.get_stock_quote_history import GetStockQuoteHistoryUseCase
from infrastructure.config.config_adapter import ConfigAdapter
from infrastructure.logging.logger_adapter import Logger
from infrastructure.repositories.repository_stock_quote import RepositoryStockQuote
from infrastructure.uow.uow import UowFactory


@lru_cache
def get_config():
    return ConfigAdapter()


@lru_cache
def get_logger():
    return Logger(get_config())


@lru_cache
def get_stock_quote_repository():
    return RepositoryStockQuote(config=get_config(), logger=get_logger())


@lru_cache
def get_uow_factory():
    repo = get_stock_quote_repository()
    return UowFactory(session_factory=repo.Session)


@lru_cache
def get_stock_quote_history_usecase() -> GetStockQuoteHistoryUseCase:
    return GetStockQuoteHistoryUseCase(
        uow_factory=get_uow_factory(),
        repository=get_stock_quote_repository(),
        logger=get_logger(),
    )
