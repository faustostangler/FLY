from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from domain.dtos import RawStatementDTO

from .repository_base_port import RepositoryBasePort


@runtime_checkable
class RawStatementsRepositoryPort(RepositoryBasePort[RawStatementDTO, int], Protocol):
    """Port for persisting raw statement rows."""

    def get_by_company_name(self, company_name: str) -> List[RawStatementDTO]: ...
