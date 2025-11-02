from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol, Tuple, runtime_checkable

from application.ports.uow_port import Uow
from domain.dtos.statement_ratio_dto import StatementRatioDTO
from domain.ports.repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryStatementRatioPort(RepositoryBasePort[StatementRatioDTO, int], Protocol):
    """Port definition for persisting Ratio financial statements.

    Extends RepositoryBasePort with methods specific to handling Ratio
    financial statements associated with companies.
    """

    def get_head(self, company_name: str, uow:Uow) -> Optional[Tuple[datetime, int]]:
        ...
