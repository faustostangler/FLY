from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

# Generic type variable for scraped data results
T = TypeVar("T")

from domain.ports import BaseScraperPort


@runtime_checkable
class CompanyDataScraperPort(BaseScraperPort[T], Protocol):
    """Abstraction for external company data scrapers.

    Defines the contract that any scraper implementation must follow
    to integrate with the application. This enables loose coupling
    between the core domain logic and concrete data providers.

    Type Args:
        T: The type of data object returned by the scraper
           (e.g., a DTO representing company information).
    """
