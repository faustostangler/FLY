from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class RatioDTO:
    """Canonical DTO for financial ratios persisted in long format."""

    id: Optional[int] = None
    company_id: str
    cnpj_root: Optional[str]
    date: datetime
    scope: str
    ticker: Optional[str]
    metric_code: str
    metric_name: str
    value: Optional[float]
    unit: Optional[str]
    version: str
    is_current: bool
    hash: str
    created_at: datetime
