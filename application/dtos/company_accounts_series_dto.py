from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from application.dtos.account_series_dto import AccountSeriesDTO


@dataclass(frozen=True)
class CompanyAccountsSeriesDTO:
    """Bundle of account series for a company."""

    company_name: str
    ticker: Optional[str]
    series: List[AccountSeriesDTO]
    meta: Dict[str, Any] = field(default_factory=dict)
    cache_info: Dict[str, Any] = field(default_factory=dict)
