from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from application.ports.uow_port import Uow
from domain.dtos.statement_raw_dto import StatementRawDTO

from .repository_base_port import RepositoryBasePort


@runtime_checkable
class RepositoryStatementsRawPort(RepositoryBasePort[StatementRawDTO, int], Protocol):
    """Port interface for managing raw statement persistence.

    Extends the base repository port to handle `StatementRawDTO` entities,
    providing both standard CRUD operations and domain-specific queries.

    Methods:
        get_by_company_name(company_name: str) -> List[StatementRawDTO]:
            Retrieve all raw statements belonging to the given company.
    """

    # def get_by_company_name(self, company_name: str) -> List[StatementRawDTO]: ...
    def get_company_year_view(
        self,
        *,
        company_name: str,
        year: int,
        uow: Uow,
    ) -> List[StatementRawDTO]:...
