"""Utilities for handling statement versioning."""

from __future__ import annotations

from typing import Dict, List, Tuple

from domain.dto.raw_statement_dto import RawStatementDTO


def _version_number(version: str | None) -> int:
    """Return numeric part of ``version`` or ``-1`` when invalid."""
    if not version:
        return -1
    digits = "".join(ch for ch in version if ch.isdigit())
    return int(digits) if digits.isdigit() else -1


def filter_latest_versions(rows: List[RawStatementDTO]) -> List[RawStatementDTO]:
    """Return only the latest version per quarter from ``rows``."""
    groups: Dict[Tuple[str, str, str, str, str], List[RawStatementDTO]] = {}
    for row in rows:
        key = (
            row.company_name or "",
            row.account,
            row.grupo,
            row.quadro,
            row.quarter or "",
        )
        groups.setdefault(key, []).append(row)

    result: List[RawStatementDTO] = []
    for candidates in groups.values():
        latest = max(candidates, key=lambda r: _version_number(r.version))
        result.append(latest)
    return result
