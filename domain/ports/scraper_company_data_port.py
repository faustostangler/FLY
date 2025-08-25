from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from domain.ports.scraper_base_port import ScraperBasePort

# Generic type variable for scraped data results
T = TypeVar("T")



@runtime_checkable
class ScraperCompanyDataPort(ScraperBasePort[T], Protocol):
    """Abstraction for external company data scrapers.

    Defines the contract that any scraper implementation must follow
    to integrate with the application. This enables loose coupling
    between the core domain logic and concrete data providers.

    Type Args:
        T: The type of data object returned by the scraper
           (e.g., a DTO representing company information).
    """
