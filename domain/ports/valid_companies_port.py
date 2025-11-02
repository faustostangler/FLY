"""Unified port for the Valid Companies projection (read + write)."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Sequence
from application.ports.uow_port import Uow
from domain.dtos.valid_company_read_model_dto import ValidCompanyReadModelDTO


class ValidCompaniesPort(ABC):
    """Contract for reading and writing the valid companies projection."""

    # === Read operations ===
    @abstractmethod
    def list(
        self,
        *,
        uow: Uow,
        cvm_code: str | None = None,
        company_name: str | None = None,
        segment: str | None = None,
    ) -> list[ValidCompanyReadModelDTO]:
        """Return all valid companies matching the given filters."""

    # === Write operations ===
    @abstractmethod
    def replace_all(
        self,
        items: Sequence[ValidCompanyReadModelDTO],
        *,
        uow: Uow,
    ) -> None:
        """Replace all projection entries with the provided items."""
