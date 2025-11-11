from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pandas as pd

from domain.dtos.cache_ratios_result_dto import CacheRatiosResultDTO


@dataclass(frozen=True, kw_only=True)
class CompanyRatiosFrameDTO:
    """DataFrame of ratios for a company plus cache metadata."""

    company_name: str
    ticker: Optional[str]
    frame: pd.DataFrame
    cache_info: CacheRatiosResultDTO
    meta: Dict[str, Any] = field(default_factory=dict)
