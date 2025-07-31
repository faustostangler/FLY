from datetime import datetime
from typing import Dict, List, Tuple

from domain.dto.raw_statement_dto import RawStatementDTO
from domain.utils.math_utils import detect_missing_quarters


def validate_quarter_completeness(
    rows: List[RawStatementDTO]
) -> Dict[Tuple[str, str, str, str, str], List[datetime]]:
    """
    For each version‐group in the given raw rows, detect which quarter‐end dates are missing.
    """
    groups: Dict[Tuple[str,str,str,str,str], List[datetime]] = {}
    for row in rows:
        if not row.quarter:
            continue
        dt = datetime.fromisoformat(row.quarter)
        key = (
            row.company_name or "",
            row.account,
            row.grupo,
            row.quadro,
            row.version or "",
        )
        groups.setdefault(key, []).append(dt)

    missing_by_group: Dict[Tuple[str,str,str,str,str], List[datetime]] = {}
    for key, date_list in groups.items():
        unique_sorted = sorted(set(date_list))
        missing = detect_missing_quarters(unique_sorted)
        if missing:
            missing_by_group[key] = missing

    return missing_by_group
