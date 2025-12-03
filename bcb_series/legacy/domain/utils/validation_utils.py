from datetime import datetime
from typing import Dict, List, Optional, Protocol, Sequence, Tuple

from domain.utils.math_utils import detect_missing_quarters


class _QuarterLike(Protocol):
    @property
    def company_name(self) -> Optional[str]: ...
    @property
    def account(self) -> str: ...
    @property
    def grupo(self) -> str: ...
    @property
    def quadro(self) -> str: ...
    @property
    def quarter(self) -> Optional[str]: ...


def validate_quarter_completeness(
    rows: Sequence[_QuarterLike],
) -> Dict[Tuple[str, str, str, str, str], List[datetime]]:
    """
    Para cada grupo de versão nas linhas fornecidas, detecta quais datas de fim de trimestre estão faltando.
    """
    groups: Dict[Tuple[str, str, str, str, str], List[datetime]] = {}
    for row in rows:
        if not row.quarter:
            continue
        dt = datetime.fromisoformat(row.quarter)
        key = (
            row.company_name or "",
            row.account,
            row.grupo,
            row.quadro,
            "",  # row.version ou ""
        )
        groups.setdefault(key, []).append(dt)

    missing_by_group: Dict[Tuple[str, str, str, str, str], List[datetime]] = {}
    for key, date_list in groups.items():
        unique_sorted = sorted(set(date_list))
        missing = detect_missing_quarters(unique_sorted)
        if missing:
            missing_by_group[key] = missing

    return missing_by_group
