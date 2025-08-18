"""Port definitions for external company data sources."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar, runtime_checkable

# from domain.dtos import CompanyDataDTO
from domain.ports import BaseScraperPort

T = TypeVar("T")


@runtime_checkable
class CompanyDataScraperPort(BaseScraperPort[T], Protocol):
    """Port for external company data providers."""
