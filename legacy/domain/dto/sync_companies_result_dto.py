"""DTO summarizing the results of company synchronization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class SyncCompanyDataResultDTO:
    """Summary information returned by :class:`SyncCompanyDataUseCase`."""

    processed_count: int
    skipped_count: int
    bytes_downloaded: int
    elapsed_time: float
    warnings: Optional[List[str]] = None
