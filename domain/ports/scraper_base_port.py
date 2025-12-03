from __future__ import annotations

from datetime import datetime
from typing import (
    Generic,
    Iterable,
    List,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)

from application.ports.uow_port import Uow

# Type variable representing the entity type being scraped
T = TypeVar("T")
ExistingItem = Union[
    str,
    int,
    Tuple[str, str],
    Tuple[str, str, datetime | None, datetime],
]


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
        existing_codes: Optional[Iterable[ExistingItem]] = None,
        save_callback: Optional[SaveCallback[T]] = None,
        **kwargs,
    ) -> List[T]:
        """Fetch a collection of items from an external source.

        Args:
            threshold (Optional[int]): Maximum number of items to fetch.
                If None, no limit is applied.
            existing_codes (Optional[Iterable[ExistingItem]]): Identifiers to
                exclude from the scraping process.
            save_callback (Optional[SaveCallback[T]]): Optional callback
                function executed after fetching, typically for persisting
                results. The callback receives the buffered items and the
                active unit of work used for persistence.
            **kwargs: Additional keyword arguments passed to the
                implementation.

        Returns:
            List[T]: A list of scraped domain entities.
        """
        ...

    def get_metrics(self) -> int:
        """Retrieve metrics related to the scraping process."""
        ...
