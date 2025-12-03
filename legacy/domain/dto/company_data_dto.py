"""Publicly exposed company DTO used throughout the application."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .raw_company_data_dto import CompanyDataRawDTO


@dataclass(frozen=True, kw_only=True)
class CompanyDataDTO:
    """Structured company data extracted from the exchange."""

    id: Optional[int] = None
    cvm_code: Optional[str] = None
    issuing_company: Optional[str] = None
    trading_name: Optional[str] = None
    company_name: Optional[str]

    cnpj: Optional[str] = None

    ticker_codes: Optional[str] = None
    isin_codes: Optional[str] = None
    other_codes: Optional[str] = None

    industry_sector: Optional[str] = None
    industry_subsector: Optional[str] = None
    industry_segment: Optional[str] = None
    industry_classification: Optional[str] = None
    industry_classification_eng: Optional[str] = None
    activity: Optional[str] = None

    company_segment: Optional[str] = None
    company_segment_eng: Optional[str] = None
    company_category: Optional[str] = None
    company_type: Optional[str] = None

    listing_segment: Optional[str] = None
    registrar: Optional[str] = None
    website: Optional[str] = None
    institution_common: Optional[str] = None
    institution_preferred: Optional[str] = None

    market: Optional[str] = None
    status: Optional[str] = None
    market_indicator: Optional[str] = None

    code: Optional[str] = None
    has_bdr: Optional[bool] = None
    type_bdr: Optional[str] = None
    has_quotation: Optional[bool] = None
    has_emissions: Optional[bool] = None

    date_quotation: Optional[datetime] = None
    last_date: Optional[datetime] = None
    listing_date: Optional[datetime] = None

    @staticmethod
    def from_dict(raw: dict) -> "CompanyDataDTO":
        """Build an immutable DTO from a raw dictionary."""

        # Map incoming keys to the canonical DTO fields. Alternative names are
        # also handled for backward compatibility with existing scrapers.
        return CompanyDataDTO(
            id=raw.get("id"),
            cvm_code=raw.get("cvm_code") or raw.get("codeCVM"),
            issuing_company=raw.get("issuing_company") or raw.get("issuingCompany"),
            trading_name=raw.get("trading_name") or raw.get("tradingName"),
            company_name=raw.get("company_name") or raw.get("companyName"),
            cnpj=raw.get("cnpj"),
            ticker_codes=raw.get("ticker_codes"),
            isin_codes=raw.get("isin_codes"),
            other_codes=raw.get("other_codes"),
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
    def from_raw(raw: CompanyDataRawDTO) -> "CompanyDataDTO":
        """Build a ``CompanyDataDTO`` from a ``CompanyDataRawDTO`` instance."""

        # Encode list of :class:`CodeDTO` objects as a JSON string if present.
        other_codes = (
            json.dumps([{"code": c.code, "isin": c.isin} for c in raw.other_codes])
            if raw.other_codes
            else None
        )

        # Instantiate the immutable DTO using the serialized raw values
        return CompanyDataDTO(
            id=None,
            cvm_code=raw.cvm_code,
            issuing_company=raw.issuing_company,
            trading_name=raw.trading_name,
            company_name=raw.company_name,
            cnpj=raw.cnpj,
            ticker_codes=json.dumps(raw.ticker_codes) if raw.ticker_codes else None,
            isin_codes=json.dumps(raw.isin_codes) if raw.isin_codes else None,
            other_codes=other_codes,
            industry_sector=raw.industry_sector,
            industry_subsector=raw.industry_subsector,
            industry_segment=raw.industry_segment,
            industry_classification=raw.industry_classification,
            industry_classification_eng=raw.industry_classification_eng,
            activity=raw.activity,
            company_segment=raw.company_segment,
            company_segment_eng=raw.company_segment_eng,
            company_category=raw.company_category,
            company_type=raw.company_type,
            listing_segment=raw.listing_segment,
            registrar=raw.registrar,
            website=raw.website,
            institution_common=raw.institution_common,
            institution_preferred=raw.institution_preferred,
            market=raw.market,
            status=raw.status,
            market_indicator=raw.market_indicator,
            code=raw.code,
            has_bdr=raw.has_bdr,
            type_bdr=raw.type_bdr,
            has_quotation=raw.has_quotation,
            has_emissions=raw.has_emissions,
            date_quotation=raw.date_quotation,
            last_date=raw.last_date,
            listing_date=raw.listing_date,
        )
