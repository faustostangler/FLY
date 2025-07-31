"""Validation helpers for raw statement rows."""

from __future__ import annotations

from datetime import datetime
from typing import List

from domain.dto.raw_statement_dto import RawStatementDTO
from domain.utils.math_utils import detect_missing_quarters, extract_sorted_quarters


def validate_quarter_completeness(rows: List[RawStatementDTO]) -> List[datetime]:
    """Return any missing quarter-end dates across ``rows``."""
    groups = {}
    for row in rows:
        dt = datetime.fromisoformat(row.quarter) if row.quarter else None
        key = (
            row.company_name or "",
            row.account,
            row.grupo,
            row.quadro,
            row.version or "",
        )
        groups.setdefault(key, []).append((dt, row))

    quarters = extract_sorted_quarters(groups)
    return detect_missing_quarters(quarters)
