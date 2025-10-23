from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence, runtime_checkable

# from application.ports.uow_port import Uow
from domain.dtos.stock_quote_dto import StockQuoteDTO
from domain.ports.repository_base_port import RepositoryBasePort
from application.ports.uow_port import Uow


@runtime_checkable
class RepositoryStockQuotePort(RepositoryBasePort[StockQuoteDTO, int], Protocol):
    """
    """
    def get_last_date(self, *, ticker: str, uow: Uow):...

    def list_between_dates(
        self,
        *,
        company_name: str,
        start: datetime,
        end: datetime,
        uow: Uow,
    ) -> Sequence[StockQuoteDTO]:
        """Return the adjusted daily quotes for the given company and period."""
