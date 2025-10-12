from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable
from domain.dtos.statement_fetched_dto import StatementFetchedDTO

from .repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryStatementFetchedPort(RepositoryBasePort[StatementFetchedDTO, int], Protocol):
    """Port definition for persisting fetched financial statements.

    Extends RepositoryBasePort with methods specific to handling fetched
    financial statements associated with companies.
    """

    def get_by_company_name(self, company_name: str) -> Sequence[StatementFetchedDTO]: ...

