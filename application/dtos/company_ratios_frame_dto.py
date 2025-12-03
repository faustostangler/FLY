from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pandas as pd

from domain.dtos.cache_ratios_result_dto import CacheRatiosResultDTO


@dataclass(frozen=True)
class CompanyRatiosFrameDTO:
    """Raw ratios frame for a single company."""

    company_name: str
    frame: pd.DataFrame
    cache_info: CacheRatiosResultDTO
    ticker: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


__all__ = ["CompanyRatiosFrameDTO"]

