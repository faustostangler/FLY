from __future__ import annotations

from dataclasses import dataclass

from domain.dtos.ratios_cache_entry_dto import RatiosCacheEntryDTO


@dataclass(frozen=True, kw_only=True)
class RatiosCacheResultDTO:
    """Outcome of attempting to obtain ratios data from the cache."""

    company_name: str
    cache_key: str
    hit: bool
    entry: RatiosCacheEntryDTO
