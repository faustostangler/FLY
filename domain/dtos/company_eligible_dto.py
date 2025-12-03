"""DTO representing the eligible company read-model projection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Tuple

from domain.dtos.company_data_dto import CodeDTO
from domain.entities import EligibleCompany


@dataclass(frozen=True)
class CompanyEligibleDTO:
    """Data transfer object for the eligible companies projection."""

    id: int | None = None
    cvm_code: str | None = None
    issuing_company: str | None = None
    trading_name: str | None = None
    company_name: str | None = None
    cnpj: str | None = None
    ticker_codes: Tuple[str, ...] = field(default_factory=tuple)
    isin_codes: Tuple[str, ...] = field(default_factory=tuple)
    other_codes: Tuple[CodeDTO, ...] = field(default_factory=tuple)
    market: str | None = None

    industry_sector: str | None = None
    industry_subsector: str | None = None
    industry_segment: str | None = None
    industry_classification: str | None = None
    industry_classification_eng: str | None = None
    activity: str | None = None

    company_segment: str | None = None
    company_segment_eng: str | None = None
    company_category: str | None = None
    company_type: str | None = None

    listing_segment: str | None = None
    registrar: str | None = None
    website: str | None = None
    institution_common: str | None = None
    institution_preferred: str | None = None

    status: str | None = None
    market_indicator: str | None = None
    code: str | None = None
    has_bdr: bool | None = None
    type_bdr: str | None = None
    has_quotation: bool | None = None
    has_emissions: bool | None = None

    date_quotation: datetime | None = None
    last_date: datetime | None = None
    listing_date: datetime | None = None

    reason: str | None = None

    @staticmethod
    def from_entity(entity: EligibleCompany) -> "CompanyEligibleDTO":
        return CompanyEligibleDTO(
            id=entity.id,
            company_name=entity.company_name,
            cvm_code=entity.cvm_code,
            issuing_company=entity.issuing_company,
            ticker_codes=entity.ticker_codes,
            isin_codes=entity.isin_codes,
            other_codes=entity.other_codes,
            market=entity.market,
            reason=entity.reason,
            trading_name=entity.trading_name,
            cnpj=entity.cnpj,
            industry_sector=entity.industry_sector,
            industry_subsector=entity.industry_subsector,
            industry_segment=entity.industry_segment,
            industry_classification=entity.industry_classification,
            industry_classification_eng=entity.industry_classification_eng,
            activity=entity.activity,
            company_segment=entity.company_segment,
            company_segment_eng=entity.company_segment_eng,
            company_category=entity.company_category,
            company_type=entity.company_type,
            listing_segment=entity.listing_segment,
            registrar=entity.registrar,
            website=entity.website,
            institution_common=entity.institution_common,
            institution_preferred=entity.institution_preferred,
            status=entity.status,
            market_indicator=entity.market_indicator,
            code=entity.code,
            has_bdr=entity.has_bdr,
            type_bdr=entity.type_bdr,
            has_quotation=entity.has_quotation,
            has_emissions=entity.has_emissions,
            date_quotation=entity.date_quotation,
            last_date=entity.last_date,
            listing_date=entity.listing_date,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Expose a plain dictionary for dataframe creation and serialization."""

        return {
            "id": self.id,
            "cvm_code": self.cvm_code,
            "issuing_company": self.issuing_company,
            "trading_name": self.trading_name,
            "company_name": self.company_name,
            "cnpj": self.cnpj,
            "ticker_codes": list(self.ticker_codes),
            "isin_codes": list(self.isin_codes),
            "other_codes": [
                {"code": code.code, "isin": code.isin}
                for code in self.other_codes
            ],
            "market": self.market,
            "industry_sector": self.industry_sector,
            "industry_subsector": self.industry_subsector,
            "industry_segment": self.industry_segment,
            "industry_classification": self.industry_classification,
            "industry_classification_eng": self.industry_classification_eng,
            "activity": self.activity,
            "company_segment": self.company_segment,
            "company_segment_eng": self.company_segment_eng,
            "company_category": self.company_category,
            "company_type": self.company_type,
            "listing_segment": self.listing_segment,
            "registrar": self.registrar,
            "website": self.website,
            "institution_common": self.institution_common,
            "institution_preferred": self.institution_preferred,
            "status": self.status,
            "market_indicator": self.market_indicator,
            "code": self.code,
            "has_bdr": self.has_bdr,
            "type_bdr": self.type_bdr,
            "has_quotation": self.has_quotation,
            "has_emissions": self.has_emissions,
            "date_quotation": self.date_quotation,
            "last_date": self.last_date,
            "listing_date": self.listing_date,
            "reason": self.reason,
        }
