from __future__ import annotations

from typing import Protocol, runtime_checkable, List

from application.ports.uow_port import Uow

# from application.ports.uow_port import Uow
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.ports.repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryStockQuotePort(RepositoryBasePort[StockQuoteDTO, int], Protocol):
    """
    """
    def get_last_date(self, *, ticker: str, uow: Uow):...

    def get_history(
        self,
        *,
        ticker: str,
        limit: int | None,
        uow: Uow,
    ) -> List[StockQuoteDTO]: ...
