from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from domain.dtos import RawStatementDTO

from .repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryStatementsRawPort(RepositoryBasePort[RawStatementDTO, int], Protocol):
    """Port interface for managing raw statement persistence.

    Extends the base repository port to handle `RawStatementDTO` entities,
    providing both standard CRUD operations and domain-specific queries.

    Methods:
        get_by_company_name(company_name: str) -> List[RawStatementDTO]:
            Retrieve all raw statements belonging to the given company.
    """

    def get_by_company_name(self, company_name: str) -> List[RawStatementDTO]: ...
