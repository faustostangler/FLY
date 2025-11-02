"""Port definition for persisting the valid companies projection."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from application.ports.uow_port import Uow
from domain.dtos.valid_company_read_model_dto import ValidCompanyReadModelDTO


@runtime_checkable
class ValidCompaniesWritePort(Protocol):
    """Write port exposing idempotent replace operations for the projection."""

    def replace_all(
        self,
        items: Sequence[ValidCompanyReadModelDTO],
        *,
        uow: Uow,
    ) -> None:
        """Atomically replace the projection with the provided items."""

