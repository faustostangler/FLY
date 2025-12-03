from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import pandas as pd

from domain.dtos.cache_ratios_entry_dto import CacheRatiosEntryDTO

if TYPE_CHECKING:
    from domain.dtos.cache_ratios_context_dto import CacheRatiosContextDTO


@runtime_checkable
class CacheRatiosPort(Protocol):
    """Port that abstracts the storage used to cache ratio calculations."""

    def initialize(self) -> None:
        """Ensure the underlying cache storage is ready for use."""

    def load(self, cache_key: str) -> tuple[pd.DataFrame, CacheRatiosEntryDTO] | None:
        """Retrieve a cached DataFrame and its metadata."""

    def store(
        self,
        *,
        context: "CacheRatiosContextDTO",
        df: pd.DataFrame,
        company_name: str,
    ) -> CacheRatiosEntryDTO:
        """Persist the DataFrame in the cache and return its metadata."""

    def invalidate_outdated(self, *, code_hash: str) -> None:
        """Remove cache artifacts that belong to outdated code versions."""
