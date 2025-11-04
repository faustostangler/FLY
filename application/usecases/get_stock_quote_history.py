from typing import List

from application.ports.logger_port import LoggerPort
from application.ports.uow_port import UowFactoryPort
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.ports.repository_stock_quote_port import RepositoryStockQuotePort


class GetStockQuoteHistoryUseCase:
    def __init__(
        self,
        *,
        uow_factory: UowFactoryPort,
        repository: RepositoryStockQuotePort,
        logger: LoggerPort,
    ) -> None:
        self.uow_factory = uow_factory
        self.repository = repository
        self.logger = logger

    def __call__(self, *, ticker: str, limit: int | None = None) -> List[StockQuoteDTO]:
        with self.uow_factory() as uow:
            quotes = self.repository.get_history(
                ticker=ticker,
                limit=limit,
                uow=uow,
            )
            uow.commit()

        self.logger.log(
            f"Loaded {len(quotes)} stock quotes for {ticker}",
            level="info",
        )
        return quotes
