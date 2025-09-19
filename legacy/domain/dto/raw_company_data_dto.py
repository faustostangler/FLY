"""Data transfer objects for raw company information."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class CodeDTO:
    """Represents a pair of ticker/ISIN codes."""

    code: Optional[str]
    isin: Optional[str]


@dataclass(frozen=True)
class CompanyDataListingDTO:
    """DTO for base company data from the list endpoint."""

    cvm_code: Optional[str]
    issuing_company: Optional[str]
    company_name: Optional[str]
    trading_name: Optional[str]
    cnpj: Optional[str]
    market_indicator: Optional[str]
    type_bdr: Optional[str]
    listing_date: Optional[datetime]
    status: Optional[str]
    segment: Optional[str]
    segment_eng: Optional[str]
    company_type: Optional[str]
    market: Optional[str]

    @staticmethod
    def from_dict(raw: dict) -> "CompanyDataListingDTO":
        """Create a listing DTO from a raw dictionary."""

        # Directly map the expected keys from the raw payload.
        return CompanyDataListingDTO(
            cvm_code=raw.get("codeCVM"),
            issuing_company=raw.get("issuingCompany"),
            company_name=raw.get("companyName"),
            trading_name=raw.get("tradingName"),
            cnpj=raw.get("cnpj"),
            market_indicator=raw.get("marketIndicator"),
            type_bdr=raw.get("typeBDR"),
            listing_date=raw.get("dateListing"),
            status=raw.get("status"),
            segment=raw.get("segment"),
            segment_eng=raw.get("segmentEng"),
            company_type=raw.get("type"),
            market=raw.get("market"),
        )


@dataclass(frozen=True)
class CompanyDataDetailDTO:
    """DTO for detailed company data from the detail endpoint."""

    issuing_company: Optional[str]
    company_name: Optional[str]
    trading_name: Optional[str]
    cnpj: Optional[str]
    industry_classification: Optional[str]
    industry_classification_eng: Optional[str]
    activity: Optional[str]
    website: Optional[str]
    has_quotation: Optional[bool]
    status: Optional[str]
    market_indicator: Optional[str]
    market: Optional[str]
    institution_common: Optional[str]
    institution_preferred: Optional[str]
    code: Optional[str]
    cvm_code: Optional[str]
    last_date: Optional[datetime]
    other_codes: List[CodeDTO]
    has_emissions: Optional[bool]
    has_bdr: Optional[bool]
    type_bdr: Optional[str]
    company_category: Optional[str]
    date_quotation: Optional[datetime]

    listing_segment: Optional[str]
    registrar: Optional[str]

    @staticmethod
    def from_dict(raw: dict) -> "CompanyDataDetailDTO":
        """Parse a detailed company payload into a DTO."""

        # ``otherCodes`` may come as a serialized JSON string; normalize to list
        other_codes = raw.get("otherCodes") or []
        if isinstance(other_codes, str):
            other_codes = json.loads(other_codes)

        # Convert dictionaries to :class:`CodeDTO` instances
        code_dtos = [
            CodeDTO(code=c.get("code"), isin=c.get("isin")) for c in other_codes
        ]

        # Populate the DTO using values from the payload
        company_data_detail_dto = CompanyDataDetailDTO(
            issuing_company=raw.get("issuingCompany"),
            company_name=raw.get("companyName"),
            trading_name=raw.get("tradingName"),
            cnpj=raw.get("cnpj"),
            industry_classification=raw.get("industryClassification"),
            industry_classification_eng=raw.get("industryClassificationEng"),
            activity=raw.get("activity"),
            website=raw.get("website"),
            has_quotation=raw.get("hasQuotation"),
            status=raw.get("status"),
            market_indicator=raw.get("marketIndicator"),
            market=raw.get("market"),
            institution_common=raw.get("institutionCommon"),
            institution_preferred=raw.get("institutionPreferred"),
            code=raw.get("code"),
            cvm_code=raw.get("codeCVM"),
            last_date=raw.get("lastDate"),
            other_codes=code_dtos,
            has_emissions=raw.get("hasEmissions"),
            has_bdr=raw.get("hasBDR"),
            type_bdr=raw.get("typeBDR"),
            company_category=raw.get("describleCategoryBVMF"),
            date_quotation=raw.get("dateQuotation"),
            listing_segment=raw.get("listingSegment"),
            registrar=raw.get("registrar"),
        )
        # Return the populated DTO instance
        return company_data_detail_dto


@dataclass(frozen=True)
class CompanyDataRawDTO:
    """Raw parsed data returned by the scraper before mapping to the domain."""

    cvm_code: Optional[str]
    issuing_company: Optional[str]
    trading_name: Optional[str]
    company_name: Optional[str]
    cnpj: Optional[str]

    ticker_codes: List[str]
    isin_codes: List[str]
    other_codes: List[CodeDTO]

    industry_sector: Optional[str]
    industry_subsector: Optional[str]
    industry_segment: Optional[str]
    industry_classification: Optional[str]
    industry_classification_eng: Optional[str]
    activity: Optional[str]

    company_segment: Optional[str]
    company_segment_eng: Optional[str]
    company_category: Optional[str]
    company_type: Optional[str]

    listing_segment: Optional[str]
    registrar: Optional[str]
    website: Optional[str]
    institution_common: Optional[str]
    institution_preferred: Optional[str]

    market: Optional[str]
    status: Optional[str]
    market_indicator: Optional[str]

    code: Optional[str]
    has_bdr: Optional[bool]
    type_bdr: Optional[str]
    has_quotation: Optional[bool]
    has_emissions: Optional[bool]

    date_quotation: Optional[datetime]
    last_date: Optional[datetime]
    listing_date: Optional[datetime]
