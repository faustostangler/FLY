from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass(frozen=True, kw_only=True)
class RatioRecordDTO:
    """Represents a computed financial ratio aligned to a common calendar."""

    company_name: str
    ticker: str
    date: datetime
    ratio_code: str
    ratio_name: str
    value: float
    components: Dict[str, float] = field(default_factory=dict)
    source_indicator: Optional[str] = None
