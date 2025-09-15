from __future__ import annotations

from typing import Callable, Generic, List, Optional, Protocol, TypeVar, runtime_checkable
from application.ports.uow_port import Uow

# Type variable representing the entity type being scraped
T = TypeVar("T")


class SaveCallback(Protocol, Generic[T]):
    def __call__(self, items: List[T], *, uow: Uow) -> None: ...
    

@runtime_checkable
class ScraperBasePort(Protocol, Generic[T]):
    """Generic port interface for external data scrapers.

    This protocol defines the contract that all scraper implementations
    must follow to integrate with the system. It is parameterized by
    a generic type `T` representing the domain entity being scraped.
    """

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        existing_codes: Optional[List[str]] = None,
        save_callback: Optional[Callable[[List[T]], None]] = None,
        **kwargs,
    ) -> List[T]:
        """Fetch a collection of items from an external source.

        Args:
            threshold (Optional[int]): Maximum number of items to fetch.
                If None, no limit is applied.
            existing_codes (Optional[List[str]]): Identifiers to exclude
                from the scraping process.
            save_callback (Optional[Callable[[List[T]], None]]): Optional
                callback function executed after fetching, typically for
                persisting results.
            **kwargs: Additional keyword arguments passed to the
                implementation.

        Returns:
            List[T]: A list of scraped domain entities.
        """
        ...

    def get_metrics(self) -> int:
        """Retrieve metrics related to the scraping process."""
        ...
