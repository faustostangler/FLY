"""Utilities for predicting upcoming NSD identifiers."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from domain.ports import RepositoryNsdPort


def _find_next_probable_nsd(
    repository: RepositoryNsdPort,
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
    last_nsd = None
    max_date = None
    window_start = None
    recent_by_date: dict[datetime, int] = {}
    recent_count = 0
    min_date = None
    total_count = 0
    overall_min_date = None

    for record in repository.iter_all():
        nsd_int = int(record.nsd)
        if last_nsd is None or nsd_int > last_nsd:
            last_nsd = nsd_int

        if record.sent_date is None:
            continue

        total_count += 1
        if overall_min_date is None or record.sent_date < overall_min_date:
            overall_min_date = record.sent_date

        if max_date is None or record.sent_date > max_date:
            max_date = record.sent_date
            window_start = max_date - timedelta(days=window_days)
            outdated = [d for d in recent_by_date if d < window_start]
            for d in outdated:
                recent_count -= recent_by_date.pop(d)
                if d == min_date:
                    min_date = min(recent_by_date) if recent_by_date else None

        if window_start is not None and record.sent_date >= window_start:
            recent_by_date[record.sent_date] = (
                recent_by_date.get(record.sent_date, 0) + 1
            )
            recent_count += 1
            if min_date is None or record.sent_date < min_date:
                min_date = record.sent_date

    if last_nsd is None or max_date is None:
        return []

    if recent_count == 0:
        recent_count = total_count
        min_date = overall_min_date

    if recent_count == 0 or min_date is None:
        return []

    days_span = max((max_date - min_date).days, 1)
    daily_avg = recent_count / days_span
    days_since_last = max((datetime.utcnow() - max_date).days, 0)
    estimate = int(daily_avg * days_since_last * safety_factor)

    return [last_nsd + i for i in range(1, estimate + 1)]
