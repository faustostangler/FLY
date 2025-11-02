"""Domain entity representing a valid company for ratios processing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ValidCompany:
    """Immutable representation of a company deemed valid for processing."""

    company_name: str
    cvm_code: str | None
    ticker_codes: Tuple[str, ...]
    reason: str

    trading_name: str | None = None
    industry_sector: str | None = None
    industry_subsector: str | None = None
    industry_segment: str | None = None
    company_segment: str | None = None
