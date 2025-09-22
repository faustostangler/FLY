from __future__ import annotations

from typing import Protocol, runtime_checkable

# from application.ports.uow_port import Uow
from domain.dtos.stock_value_dto import StockQuoteDTO
from domain.ports.repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryStockQuotePort(RepositoryBasePort[StockQuoteDTO, int], Protocol):
    """
    """
