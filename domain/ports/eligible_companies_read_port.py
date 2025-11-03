"""Read port for the eligible companies projection."""

from __future__ import annotations

from abc import ABC, abstractmethod

from application.ports.uow_port import Uow
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.dtos.eligible_companies_result_dto import EligibleCompaniesResultDTO


class EligibleCompaniesReadPort(ABC):
    """Expose read-only operations for the eligible companies projection."""

    @abstractmethod
    def get_current(self, *, uow: Uow) -> EligibleCompaniesResultDTO | None:
        """Return metadata for the current projection, if any."""

    @abstractmethod
    def list_current_companies(self, *, uow: Uow) -> list[CompanyEligibleDTO]:
        """Return the companies that belong to the current projection."""

    @abstractmethod
    def get_by_company_name(
        self,
        company_name: str,
        *,
        uow: Uow,
    ) -> CompanyEligibleDTO | None:
        """Return the projection entry for the given company name, if available."""

