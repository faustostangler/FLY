from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from application.ports.uow_port import Uow
from domain.dtos.quarter_price_dto import QuarterPriceDTO
from domain.ports.repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryQuarterPricePort(RepositoryBasePort[QuarterPriceDTO, int], Protocol):
    def insert_or_update(self, dto: QuarterPriceDTO, *, uow: Uow) -> QuarterPriceDTO: ...

    def get_for_quarter(
        self,
        *,
        company_name: str,
        quarter: datetime,
        method: str,
        uow: Uow,
    ) -> QuarterPriceDTO | None: ...
