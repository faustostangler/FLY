from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.dtos import CompanyDataDTO
from domain.ports import RepositoryBasePort


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

    def get_cvm_by_name(self, company_name: str) -> str:
        """Retrieve the CVM code for a company by its name.

        Args:
            company_name (str): The official company name.

        Returns:
            str: The CVM code associated with the given company.
        """
        ...
