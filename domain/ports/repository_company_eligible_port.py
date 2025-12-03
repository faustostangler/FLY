"""Port definition for the eligible companies repository with search support."""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from application.ports.uow_port import Uow
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.ports.repository_base_port import RepositoryBasePort
from domain.value_objects.company_filters import CompanyFilterQuery


@runtime_checkable
class RepositoryCompanyEligiblePort(
    RepositoryBasePort[CompanyEligibleDTO, str], Protocol
):
    """Port abstraction for querying the eligible companies projection."""

    def search(
        self,
        query: CompanyFilterQuery,
        *,
        uow: Uow,
        limit: int | None = None,
    ) -> list[CompanyEligibleDTO]:
        """Return companies matching the structured filter query."""
        ...

    def get_all(
        self,
        *,
        uow: Uow,
        batch_size: int | None = None,
    ) -> List[CompanyEligibleDTO]:
        """Return every eligible company DTO in stable order."""
        ...
