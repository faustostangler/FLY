from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import pandas as pd

from domain.dtos.ratios_cache_entry_dto import RatiosCacheEntryDTO

if TYPE_CHECKING:
    from domain.dtos.ratios_cache_context_dto import RatiosCacheContextDTO


@runtime_checkable
class RatiosCachePort(Protocol):
    """Port that abstracts the storage used to cache ratio calculations."""

    def initialize(self) -> None:
        """Ensure the underlying cache storage is ready for use."""

    def load(self, cache_key: str) -> tuple[pd.DataFrame, RatiosCacheEntryDTO] | None:
        """Retrieve a cached DataFrame and its metadata."""

    def store(
        self,
        *,
        context: "RatiosCacheContextDTO",
        df: pd.DataFrame,
        company_name: str,
    ) -> RatiosCacheEntryDTO:
        """Persist the DataFrame in the cache and return its metadata."""

    def invalidate_outdated(self, *, code_hash: str) -> None:
        """Remove cache artifacts that belong to outdated code versions."""
