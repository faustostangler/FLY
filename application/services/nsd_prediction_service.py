from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from domain.ports import NSDRepositoryPort


def _find_next_probable_nsd(
    repository: NSDRepositoryPort,
    window_days: int = 30,
    safety_factor: float = 1.5,
) -> List[int]:
    """Estimate next NSD numbers based on historical submission rate.

    The prediction is calculated from the most recent ``window_days`` worth
    of stored records. It computes the average number of submissions per
    day and multiplies by the number of days since the last known NSD. The
    ``safety_factor`` parameter is applied to avoid underestimation.

    Args:
        repository: Data source providing access to stored NSDs.
        window_days: Number of days used to calculate the average rate.
        safety_factor: Multiplier to account for variations in publishing
            behaviour.

    Returns:
        A list of sequential NSD values likely to have been published
        after the last stored record.
    """
    records = [r for r in repository.get_all() if r.sent_date]
    if not records:
        return []

    last_nsd = max(int(r.nsd) for r in records)
    max_date = max(r.sent_date for r in records if r.sent_date is not None)
    window_start = max_date - timedelta(days=window_days)

    recent = [r for r in records if r.sent_date is not None and r.sent_date >= window_start]
    if not recent:
        recent = records

    min_date = min(r.sent_date for r in recent if r.sent_date is not None)
    days_span = max((max_date - min_date).days, 1)
    daily_avg = len(recent) / days_span

    days_since_last = max((datetime.utcnow() - max_date).days, 0)
    estimate = int(daily_avg * days_since_last * safety_factor)

    return [last_nsd + i for i in range(1, estimate + 1)]
