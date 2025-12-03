# version_utils.py
from __future__ import annotations

from typing import Dict, List, Optional, Protocol, Sequence, Tuple, TypeVar


class _VersionedStatement(Protocol):
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
    @property
    def version(self) -> Optional[str]: ...


T = TypeVar("T", bound=_VersionedStatement)


def _version_number(version: str | None) -> int:
    """Return numeric part of ``version`` or ``-1`` when invalid."""
    if not version:
        return -1
    digits = "".join(ch for ch in version if ch.isdigit())
    return int(digits) if digits.isdigit() else -1


def filter_latest_versions(rows: Sequence[T]) -> List[T]:
    """Return only the latest version per quarter from ``rows``."""
    groups: Dict[Tuple[str, str, str, str, str], List[T]] = {}
    for row in rows:
        key = (
            row.company_name or "",
            row.account,
            row.grupo,
            row.quadro,
            row.quarter or "",
        )
        groups.setdefault(key, []).append(row)

    result: List[T] = []
    for candidates in groups.values():
        latest = max(candidates, key=lambda r: _version_number(r.version))
        result.append(latest)
    return result
