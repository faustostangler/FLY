"""Common DTOs used for pagination of external data sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PageResultDTO:
    """Container for paginated fetch results and metadata."""

    items: List[Dict]
    total_pages: int
    bytes_downloaded: int
