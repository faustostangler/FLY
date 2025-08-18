from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.dtos import CompanyDataDTO
from domain.ports import RepositoryBasePort


@runtime_checkable
class CompanyDataRepositoryPort(RepositoryBasePort[CompanyDataDTO, int], Protocol):
    """Interface (port) for persistence operations related to CompanyData
    entities.

    Acts as an abstraction for the application layer to interact with
    company-related data storage, decoupling it from the actual database
    implementation.
    """

    def get_cvm_by_name(self, company_name: str) -> str: ...
