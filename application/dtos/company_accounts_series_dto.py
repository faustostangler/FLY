from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from application.dtos.account_series_dto import AccountSeriesDTO
from domain.dtos.cache_ratios_result_dto import CacheRatiosResultDTO


@dataclass(frozen=True)
class CompanyAccountsSeriesDTO:
    company_name: str
    series: List[AccountSeriesDTO]
    ticker: Optional[str] = None
    cache_info: Optional[CacheRatiosResultDTO] = None
    meta: Dict[str, Any] = field(default_factory=dict)


__all__ = ["CompanyAccountsSeriesDTO"]

