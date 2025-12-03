from __future__ import annotations

from typing import Protocol, runtime_checkable

from application.ports.uow_port import Uow
from domain.dtos.company_data_dto import CompanyDataDTO
from domain.ports.repository_base_port import RepositoryBasePort
from domain.value_objects.company_filters import CompanyFilterQuery


@runtime_checkable
class RepositoryCompanyDataPort(RepositoryBasePort[CompanyDataDTO, int], Protocol):
    """Port interface for persistence operations on CompanyData entities.

    Provides an abstraction for the application layer to interact with
    company-related storage, without depending on a concrete database
    implementation.

    Inherits from:
        RepositoryBasePort[CompanyDataDTO, int]: Base repository contract
        for CRUD operations on CompanyData entities.
    """

    def get_cvm_by_name(self, company_name: str, *, uow: Uow) -> str | None:
            """Retrieve the CVM code for a company by its name.

        Args:
            company_name (str): The official company name.

        Returns:
            str: The CVM code associated with the given company.
        """

    # # utilitário para “garantir companhia” em lote
    # def iter_existing_by_names(self, names: set[str], *, uow: Uow) -> Iterator[str]: ...

    # # já herdado de RepositoryBasePort: save_all(..., uow)

    def get_viable_companies(
        self, uow: Uow, company_names: list[str] | None = None
    ) -> dict[str, list[str]]:
        ...

    def search(
        self,
        query: CompanyFilterQuery,
        *,
        uow: Uow,
        limit: int | None = None,
    ) -> list[CompanyDataDTO]:
        """Return companies matching the structured filter query."""
