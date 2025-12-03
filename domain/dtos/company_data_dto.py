from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, List, Optional


@dataclass(frozen=True)
class CodeDTO:
    """Represents a mapping between a trading code and its ISIN."""

    # Trading code (e.g., ticker)
    code: Optional[str]

    # International Securities Identification Number
    isin: Optional[str]


@dataclass(frozen=True)
class CompanyDataListingDTO:
    """DTO for basic company information returned by the listing endpoint."""
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
    def from_dict(raw: dict[str, Any], *, cleandate: Callable[[object], datetime|None]) -> "CompanyDataListingDTO":
        """Create a listing DTO from raw dictionary data (as-is mapping)."""
        return CompanyDataListingDTO(
            cvm_code=raw.get("codeCVM"),
            issuing_company=raw.get("issuingCompany"),
            company_name=raw.get("companyName"),
            trading_name=raw.get("tradingName"),
            cnpj=raw.get("cnpj"),
            market_indicator=raw.get("marketIndicator"),
            type_bdr=raw.get("typeBDR"),
            listing_date=cleandate(raw.get("quarter")),
            status=raw.get("status"),
            segment=raw.get("segment"),
            segment_eng=raw.get("segmentEng"),
            company_type=raw.get("type"),
            market=raw.get("market"),
        )


@dataclass(frozen=True)
class CompanyDataDetailDTO:
    """DTO for detailed company information from the detail endpoint."""
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
    def from_dict(raw: dict[str, Any]) -> "CompanyDataDetailDTO":
        """Parse and normalize a raw detail payload into a DTO."""
        # Normalize "otherCodes": may arrive as JSON string or list[dict]
        other_codes_raw = raw.get("otherCodes") or []
        if isinstance(other_codes_raw, str):
            other_codes_raw = json.loads(other_codes_raw)

        code_dtos = [
            i if isinstance(i, CodeDTO) else CodeDTO(code=i.get("code"), isin=i.get("isin"))
            for i in (other_codes_raw or [])
            if isinstance(i, (dict, CodeDTO))
        ]

        return CompanyDataDetailDTO(
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


@dataclass(frozen=True)
class CompanyDataDTO:
    """Unified and normalized company data inside the hexagon."""
    id: Optional[int] = None
    cvm_code: Optional[str] = None
    issuing_company: Optional[str] = None
    trading_name: Optional[str] = None
    company_name: Optional[str] = None
    cnpj: Optional[str] = None

    # Collections must always be real lists in the domain
    ticker_codes: List[str] = field(default_factory=list)
    isin_codes: List[str] = field(default_factory=list)
    other_codes: List[CodeDTO] = field(default_factory=list)

    # Industry classification data
    industry_sector: Optional[str] = None
    industry_subsector: Optional[str] = None
    industry_segment: Optional[str] = None
    industry_classification: Optional[str] = None
    industry_classification_eng: Optional[str] = None
    activity: Optional[str] = None

    # Company-level descriptors
    company_segment: Optional[str] = None
    company_segment_eng: Optional[str] = None
    company_category: Optional[str] = None
    company_type: Optional[str] = None

    # Listing and registry data
    listing_segment: Optional[str] = None
    registrar: Optional[str] = None
    website: Optional[str] = None
    institution_common: Optional[str] = None
    institution_preferred: Optional[str] = None

    # Market information
    market: Optional[str] = None
    status: Optional[str] = None
    market_indicator: Optional[str] = None

    # Stock and BDR attributes
    code: Optional[str] = None
    has_bdr: Optional[bool] = None
    type_bdr: Optional[str] = None
    has_quotation: Optional[bool] = None
    has_emissions: Optional[bool] = None

    # Important dates
    date_quotation: Optional[datetime] = None
    last_date: Optional[datetime] = None
    listing_date: Optional[datetime] = None

    @staticmethod
    def _to_str_list(x: Any) -> List[str]:
        """Coerce None/str/list/JSON-string into List[str]."""
        if x is None:
            return []
        if isinstance(x, list):
            return [str(i) for i in x if i is not None and str(i) != ""]
        if isinstance(x, str):
            # If it's a JSON array string, parse it; otherwise treat as single item
            try:
                fetched = json.loads(x)
                if isinstance(fetched, list):
                    return [str(i) for i in fetched if i is not None and str(i) != ""]
            except json.JSONDecodeError:
                pass
            return [x] if x != "" else []
        return [str(x)]

    @staticmethod
    def _to_code_dtos(x: Any) -> List[CodeDTO]:
        """Coerce None/str(JSON list)/list[dict|CodeDTO] into List[CodeDTO]."""
        if x is None:
            return []
        if isinstance(x, str):
            try:
                x = json.loads(x)
            except json.JSONDecodeError:
                return []
        if isinstance(x, list):
            out: List[CodeDTO] = []
            for i in x:
                if isinstance(i, CodeDTO):
                    out.append(i)
                elif isinstance(i, dict):
                    out.append(CodeDTO(code=i.get("code"), isin=i.get("isin")))
            return out
        return []

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> "CompanyDataDTO":
        """Normalize raw street payload into a DTO with real lists and stable keys."""
        return CompanyDataDTO(
            id=raw.get("id"),
            cvm_code=raw.get("cvm_code") or raw.get("codeCVM"),
            issuing_company=raw.get("issuing_company") or raw.get("issuingCompany"),
            trading_name=raw.get("trading_name") or raw.get("tradingName"),
            company_name=raw.get("company_name") or raw.get("companyName"),
            cnpj=raw.get("cnpj"),
            ticker_codes=CompanyDataDTO._to_str_list(raw.get("ticker_codes")),
            isin_codes=CompanyDataDTO._to_str_list(raw.get("isin_codes")),
            other_codes=CompanyDataDTO._to_code_dtos(raw.get("other_codes")),
            industry_sector=raw.get("industry_sector"),
            industry_subsector=raw.get("industry_subsector"),
            industry_segment=raw.get("industry_segment"),
            industry_classification=raw.get("industry_classification"),
            industry_classification_eng=raw.get("industry_classification_eng"),
            activity=raw.get("activity"),
            company_segment=raw.get("company_segment"),
            company_segment_eng=raw.get("company_segment_eng"),
            company_category=raw.get("company_category"),
            company_type=raw.get("company_type"),
            listing_segment=raw.get("listing_segment"),
            registrar=raw.get("registrar"),
            website=raw.get("website"),
            institution_common=raw.get("institution_common"),
            institution_preferred=raw.get("institution_preferred"),
            market=raw.get("market"),
            status=raw.get("status"),
            market_indicator=raw.get("market_indicator"),
            code=raw.get("code"),
            has_bdr=raw.get("has_bdr"),
            type_bdr=raw.get("type_bdr"),
            has_quotation=raw.get("has_quotation"),
            has_emissions=raw.get("has_emissions"),
            date_quotation=raw.get("date_quotation"),
            last_date=raw.get("last_date"),
            listing_date=raw.get("listing_date"),
        )

    @staticmethod
    def from_raw(obj: "CompanyDataDTO" | dict[str, Any]) -> "CompanyDataDTO":
        """
        Idempotent entry point:
        - if dict, delegates to from_dict;
        - if CompanyDataDTO, returns the same object.
        """
        if isinstance(obj, CompanyDataDTO):
            return obj
        if isinstance(obj, dict):
            return CompanyDataDTO.from_dict(obj)
        raise TypeError(f"Unsupported type for CompanyDataDTO.from_raw: {type(obj).__name__}")
