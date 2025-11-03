"""DTO summarizing statement synchronization counts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StatementsSyncItemDTO:
    """Number of rows processed for a given statements source."""

    source: str
    count: int
