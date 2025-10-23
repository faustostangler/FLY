from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class QuarterPriceDTO:
    """Immutable snapshot of the aggregated price for a fiscal quarter."""

    id: Optional[int] = None
    company_name: str
    quarter: datetime
    method: str
    price: float
    asof: datetime
    currency: Optional[str] = None
    version: Optional[int] = None

