from __future__ import annotations

from dataclasses import dataclass

from .cache_ratios_entry_dto import CacheRatiosEntryDTO


@dataclass(frozen=True, kw_only=True)
class CacheRatiosResultDTO:
    """Outcome of attempting to obtain ratios data from the cache."""

    company_name: str
    cache_key: str
    hit: bool
    entry: CacheRatiosEntryDTO
