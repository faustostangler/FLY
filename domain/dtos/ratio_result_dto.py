from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Optional, Tuple


@dataclass(frozen=True, kw_only=True)
class RatioResultDTO:
    """Daily ratio computed from normalized financial and market series."""

    id: Optional[int] = None
    company_id: str
    ratio_code: str
    date: datetime
    value: float | None
    version: str
    calculation_hash: str
    input_versions: Tuple[Tuple[str, str | None], ...]
    input_hashes: Tuple[Tuple[str, str | None], ...]
    is_current: bool = True

    @staticmethod
    def serialize_mapping(data: Mapping[str, str | None]) -> Tuple[Tuple[str, str | None], ...]:
        return tuple(sorted(data.items()))
