from __future__ import annotations

from typing import Protocol, runtime_checkable

# from application.ports.uow_port import Uow
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.ports.repository_base_port import RepositoryBasePort
from application.ports.uow_port import Uow


@runtime_checkable
class RepositoryStockQuotePort(RepositoryBasePort[StockQuoteDTO, int], Protocol):
    """
    """
    def get_last_date(self, *, ticker: str, uow: Uow):...
