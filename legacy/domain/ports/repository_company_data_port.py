"""Port definitions for company persistence repositories."""

from __future__ import annotations

from abc import abstractmethod

from domain.dto.company_data_dto import CompanyDataDTO

from .repository_base_port import RepositoryBasePort


class RepositoryCompanyDataPort(RepositoryBasePort[CompanyDataDTO, int]):
    """Interface (port) for persistence operations related to CompanyData
    entities.

    Acts as an abstraction for the application layer to interact with
    company-related data storage, decoupling it from the actual database
    implementation.
    """

    @abstractmethod
    def get_cvm_by_name(self, company_name: str) -> str:
        """Dado o nome da empresa, retorna o código CVM único associado.

        Levanta ValueError se não encontrar.
        """
        raise NotImplementedError
