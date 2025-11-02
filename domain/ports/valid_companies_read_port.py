"""Port definition for querying the valid companies read-model."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from application.ports.uow_port import Uow
from domain.dtos.valid_company_read_model_dto import ValidCompanyReadModelDTO


@runtime_checkable
class ValidCompaniesReadPort(Protocol):
    """Read port exposing filters for the valid companies projection."""

    def list(
        self,
        *,
        uow: Uow,
        cvm_code: str | None = None,
        company_name: str | None = None,
        segment: str | None = None,
    ) -> list[ValidCompanyReadModelDTO]:
        """Return projected companies using optional filters."""

