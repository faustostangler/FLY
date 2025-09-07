from __future__ import annotations

from typing import Iterable, List, Protocol, runtime_checkable

from domain.dtos.statement_raw_dto import StatementRawDTO
from domain.dtos.worker_task_dto import WorkerTaskDTO

from .repository_base_port import RepositoryBasePort
from application.ports.uow_port import Uow


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
    def fetch(self, task: WorkerTaskDTO) -> Iterable[StatementRawDTO]: ...

    def get_company_year_view(
        self,
        *,
        company_id: int | str,
        year: int,
        uow: Uow,
    ) -> List[StatementRawDTO]:...
