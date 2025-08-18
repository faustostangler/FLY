from __future__ import annotations

from typing import (
    Callable,
    Generic,
    List,
    Optional,
    Protocol,
    TypeVar,
    runtime_checkable,
)

T = TypeVar("T")


@runtime_checkable
class BaseScraperPort(Protocol, Generic[T]):
    """Generic port for external data providers."""

    def fetch_all(
        self,
        threshold: Optional[int] = None,
        skip_codes: Optional[List[str]] = None,
        save_callback: Optional[Callable[[List[T]], None]] = None,
        **kwargs,
    ) -> List[T]: ...
