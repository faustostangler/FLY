from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol, runtime_checkable

from application.ports.uow_port import Uow
from domain.dtos.statement_fetched_dto import StatementFetchedDTO
from domain.ports.repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryStatementFetchedPort(RepositoryBasePort[StatementFetchedDTO, int], Protocol):
    """Port definition for persisting fetched financial statements.

    Extends RepositoryBasePort with methods specific to handling fetched
    financial statements associated with companies.
    """

    def get_head(self, company: str, *, uow: Uow) -> Optional[tuple[datetime, int]]: ...
