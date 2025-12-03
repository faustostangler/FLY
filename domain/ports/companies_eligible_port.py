"""Unified port for the eligible companies projection (read + write)."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Sequence
from application.ports.uow_port import Uow
from domain.dtos.company_eligible_dto import CompanyEligibleDTO


class CompaniesEligiblePort(ABC):
    """Contract for reading and writing the eligible companies projection."""

    # === Read operations ===
    @abstractmethod
    def list(
        self,
        *,
        uow: Uow,
        cvm_code: str | None = None,
        company_name: str | None = None,
        segment: str | None = None,
    ) -> list[CompanyEligibleDTO]:
        """Return all eligible companies matching the given filters."""

    # === Write operations ===
    @abstractmethod
    def replace_all(
        self,
        items: Sequence[CompanyEligibleDTO],
        *,
        uow: Uow,
    ) -> None:
        """Replace all projection entries with the provided items."""
