from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class CompanySearchResultDTO:
    company_name: str
    trading_name: str | None
    tickers: List[str] = field(default_factory=list)
    sector: str | None = None
    subsector: str | None = None
    segment: str | None = None
    market: str | None = None
    institution_common: str | None = None
    institution_preferred: str | None = None
    issuing_company: str | None = None
    code: str | None = None
    cnpj: str | None = None
