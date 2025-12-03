"""Math helper functions for statement processing."""

from __future__ import annotations

from datetime import datetime


def parse_quarter(quarter: str | None) -> datetime | None:
    """Return ``datetime`` fetched from ISO date string."""
    if not quarter:
        return None
    try:
        return datetime.fromisoformat(quarter)
    except ValueError:
        return None


def quarter_index(dt: datetime) -> int:
    """Return quarter number (1-4) for ``dt``."""
    return (dt.month - 1) // 3 + 1


def find_missing_quarters(dates: list[datetime]) -> list[datetime]:
    """Return the expected quarter-end dates missing from ``dates``.

    Parameters
    ----------
    dates:
        Collection of datetimes representing quarter ends or arbitrary dates.

    Returns
    -------
    list[datetime]
        Quarter-end dates that should exist between the first and last provided
        dates but are absent from ``dates``.
    """

    if not dates:
        return []

    unique_dates = sorted(set(dates))
    start = unique_dates[0]
    end = unique_dates[-1]

    def to_quarter_end(dt: datetime) -> datetime:
        month = dt.month
        if month in (1, 2, 3):
            return datetime(dt.year, 3, 31)
        if month in (4, 5, 6):
            return datetime(dt.year, 6, 30)
        if month in (7, 8, 9):
            return datetime(dt.year, 9, 30)
        return datetime(dt.year, 12, 31)

    expected: list[datetime] = []
    y, m = start.year, to_quarter_end(start).month
    current = datetime(y, m, 1)
    while current <= end:
        quarter_end = to_quarter_end(current)
        expected.append(quarter_end)
        next_month = current.month + 3
        next_year = current.year + (next_month - 1) // 12
        next_month = ((next_month - 1) % 12) + 1
        current = datetime(next_year, next_month, 1)

    actual_quarters = {to_quarter_end(dt) for dt in dates}

    return [q for q in expected if q not in actual_quarters]


def extract_sorted_quarters(groups: dict) -> list[datetime]:
    seen = set()
    quarters = []
    for items in groups.values():
        for dt, _ in items:
            if dt and dt not in seen:
                seen.add(dt)
                quarters.append(dt)
    return sorted(quarters)


def detect_missing_quarters(sorted_quarters: list[datetime]) -> list[datetime]:
    if not sorted_quarters:
        return []

    start = min(sorted_quarters)
    end = max(sorted_quarters)
    expected = []

    # Avança trimestre por trimestre
    current = datetime(start.year, start.month, start.day)
    while current <= end:
        expected.append(current)
        # Avança para o próximo trimestre
        month = current.month
        if month == 3:
            current = datetime(current.year, 6, 30)
        elif month == 6:
            current = datetime(current.year, 9, 30)
        elif month == 9:
            current = datetime(current.year, 12, 31)
        elif month == 12:
            current = datetime(current.year + 1, 3, 31)
        else:
            break  # formato inesperado

    # Compara os esperados com os reais
    return [dt for dt in expected if dt not in sorted_quarters]
