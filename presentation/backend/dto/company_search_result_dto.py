from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class CompanySearchResultDTO(BaseModel):
    company_name: str
    trading_name: Optional[str] = None
    tickers: List[str] = Field(default_factory=list)
    sector: Optional[str] = None
    subsector: Optional[str] = None
    segment: Optional[str] = None
    market: Optional[str] = None
    institution_common: Optional[str] = None
    institution_preferred: Optional[str] = None

    issuing_company: Optional[str] = None
    code: Optional[str] = None
    cnpj: Optional[str] = None
