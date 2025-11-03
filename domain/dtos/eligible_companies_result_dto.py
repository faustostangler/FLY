"""Result DTO summarizing the eligible companies projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EligibleCompaniesResultDTO:
    """Projection summary returned after running the eligible pipeline."""

    evaluated_count: int
    eligible_count: int
    version: str
    started_at: datetime
    completed_at: datetime

    @property
    def duration_seconds(self) -> float:
        """Return the elapsed seconds between start and completion."""

        return (self.completed_at - self.started_at).total_seconds()
