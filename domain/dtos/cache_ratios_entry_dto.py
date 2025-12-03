from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class CacheRatiosEntryDTO:
    """Metadata describing a cached ratios artifact."""

    cache_key: str
    file_path: str
    size_bytes: int
    created_at: datetime
    accessed_at: datetime
    access_count: int
    code_hash: str
