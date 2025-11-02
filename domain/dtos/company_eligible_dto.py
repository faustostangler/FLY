"""DTO representing the eligible company read-model projection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from domain.entities import EligibleCompany


@dataclass(frozen=True)
class CompanyEligibleDTO:
    """Data transfer object for the eligible companies projection."""

    company_name: str
    cvm_code: str | None
    ticker_codes: Tuple[str, ...]
    reason: str

    trading_name: str | None = None
    industry_sector: str | None = None
    industry_subsector: str | None = None
    industry_segment: str | None = None
    company_segment: str | None = None

    @staticmethod
    def from_entity(entity: EligibleCompany) -> "CompanyEligibleDTO":
        return CompanyEligibleDTO(
            company_name=entity.company_name,
            cvm_code=entity.cvm_code,
            ticker_codes=entity.ticker_codes,
            reason=entity.reason,
            trading_name=entity.trading_name,
            industry_sector=entity.industry_sector,
            industry_subsector=entity.industry_subsector,
            industry_segment=entity.industry_segment,
            company_segment=entity.company_segment,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Expose a plain dictionary for dataframe creation and serialization."""

        return {
            "company_name": self.company_name,
            "cvm_code": self.cvm_code,
            "ticker_codes": list(self.ticker_codes),
            "reason": self.reason,
            "trading_name": self.trading_name,
            "industry_sector": self.industry_sector,
            "industry_subsector": self.industry_subsector,
            "industry_segment": self.industry_segment,
            "company_segment": self.company_segment,
        }
