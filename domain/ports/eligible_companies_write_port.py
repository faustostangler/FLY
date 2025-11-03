"""Write port for the eligible companies projection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from application.ports.uow_port import Uow
from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.dtos.eligible_companies_command_dto import EligibleCompaniesCommandDTO
from domain.dtos.eligible_companies_result_dto import EligibleCompaniesResultDTO


class EligibleCompaniesWritePort(ABC):
    """Persist new eligible companies projection versions."""

    @abstractmethod
    def save_projection(
        self,
        *,
        uow: Uow,
        command: EligibleCompaniesCommandDTO,
        companies: Sequence[CompanyEligibleDTO],
        result: EligibleCompaniesResultDTO,
    ) -> None:
        """Persist the evaluated companies and metadata atomically."""

