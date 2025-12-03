from __future__ import annotations

import dataclasses
import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from domain.dtos.company_data_dto import CodeDTO, CompanyDataDTO
from infrastructure.models.base_model import BaseModel


class CompanyDataModel(BaseModel):
    """SQLAlchemy ORM model for the ``tbl_company`` table.

    This model maps normalized company master data into a single table and
    provides helpers to convert between the persistence layer and the
    corresponding domain DTO.

    Notes:
        - Some multi-valued fields (e.g., tickers, ISINs) are persisted as
          comma-separated strings for simplicity and later expanded back into
          lists in ``to_dto``.
        - ``other_codes`` is stored as a JSON array of objects and fetched back
          into a list of :class:`CodeDTO`.
    """

    __tablename__ = "tbl_company"

    # Surrogate primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # CVM code and legal/trade names
    cvm_code: Mapped[Optional[str]] = mapped_column()
    issuing_company: Mapped[Optional[str]] = mapped_column()
    trading_name: Mapped[Optional[str]] = mapped_column()
    company_name: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    cnpj: Mapped[Optional[str]] = mapped_column()

    # Identifier collections (tickers/ISINs/others) stored as strings
    ticker_codes: Mapped[Optional[str]] = mapped_column()
    isin_codes: Mapped[Optional[str]] = mapped_column()
    other_codes: Mapped[Optional[str]] = mapped_column()

    # Industry classification details
    industry_sector: Mapped[Optional[str]] = mapped_column()
    industry_subsector: Mapped[Optional[str]] = mapped_column()
    industry_segment: Mapped[Optional[str]] = mapped_column()
    industry_classification: Mapped[Optional[str]] = mapped_column()
    industry_classification_eng: Mapped[Optional[str]] = mapped_column()
    activity: Mapped[Optional[str]] = mapped_column()

    # Company segmentation and category metadata
    company_segment: Mapped[Optional[str]] = mapped_column()
    company_segment_eng: Mapped[Optional[str]] = mapped_column()
    company_category: Mapped[Optional[str]] = mapped_column()
    company_type: Mapped[Optional[str]] = mapped_column()

    # Listing/registrar information
    listing_segment: Mapped[Optional[str]] = mapped_column()
    registrar: Mapped[Optional[str]] = mapped_column()
    website: Mapped[Optional[str]] = mapped_column()
    institution_common: Mapped[Optional[str]] = mapped_column()
    institution_preferred: Mapped[Optional[str]] = mapped_column()

    # Market and status flags
    market: Mapped[Optional[str]] = mapped_column()
    status: Mapped[Optional[str]] = mapped_column()
    market_indicator: Mapped[Optional[str]] = mapped_column()

    # Miscellaneous identification and BDR/quotation flags
    code: Mapped[Optional[str]] = mapped_column()
    has_bdr: Mapped[Optional[bool]] = mapped_column(Boolean)
    type_bdr: Mapped[Optional[str]] = mapped_column()
    has_quotation: Mapped[Optional[bool]] = mapped_column(Boolean)
    has_emissions: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Relevant dates (quotation, last activity, listing)
    date_quotation: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    listing_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Explicit index for company_name to support fast lookups
    __table_args__ = (Index("ix_company_company_name", "company_name"),)

    @staticmethod
    def from_dto(dto: CompanyDataDTO) -> CompanyDataModel:
        """Create a :class:`CompanyDataModel` instance from a :class:`CompanyDataDTO`.

        This method normalizes multi-valued fields to string storage formats
        used by the table (comma-separated lists or JSON arrays).

        Args:
            dto (CompanyDataDTO): Source DTO carrying company attributes.

        Returns:
            CompanyDataModel: ORM model ready to be persisted.
        """

        # Helper to safely pull an attribute from the DTO with fallback None
        def attr(name: str):
            return getattr(dto, name, None)

        # Prefer provided tickers; otherwise, fall back to issuing_company as a single code
        ticker_codes = attr("ticker_codes") or (
            [] if attr("issuing_company") is None else [attr("issuing_company")]
        )

        # Ensure ISIN codes default to empty list when absent
        isin_codes = attr("isin_codes") or []

        # Pass-through for other code structures (may be list[CodeDTO] or serialized str)
        other_codes = attr("other_codes")

        # Normalize code-like fields into comma-separated strings
        def format_code_field(value):
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    fetched = json.loads(value)
                    if isinstance(fetched, list):
                        return ",".join(fetched) if fetched else None
                except json.JSONDecodeError:
                    return value
                return value
            return ",".join(value) if value else None

        # Serialize other_codes to JSON if it is a list of CodeDTO; keep string as-is
        def format_other_codes(value):
            if not value:
                return None
            if isinstance(value, str):
                return value
            return json.dumps([{"code": c.code, "isin": c.isin} for c in value])

        # Build and return the ORM model with normalized fields
        return CompanyDataModel(
            id=attr("id"),
            cvm_code=attr("cvm_code") or attr("issuing_company") or "",
            issuing_company=attr("issuing_company"),
            trading_name=attr("trading_name"),
            company_name=attr("company_name"),
            cnpj=attr("cnpj"),
            ticker_codes=format_code_field(ticker_codes),
            isin_codes=format_code_field(isin_codes),
            other_codes=format_other_codes(other_codes),
            industry_sector=attr("industry_sector"),
            industry_subsector=attr("industry_subsector"),
            industry_segment=attr("industry_segment"),
            industry_classification=attr("industry_classification"),
            industry_classification_eng=attr("industry_classification_eng"),
            activity=attr("activity"),
            company_segment=attr("company_segment"),
            company_segment_eng=attr("company_segment_eng"),
            company_category=attr("company_category"),
            company_type=attr("company_type"),
            listing_segment=attr("listing_segment"),
            registrar=attr("registrar"),
            website=attr("website"),
            institution_common=attr("institution_common"),
            institution_preferred=attr("institution_preferred"),
            market=attr("market"),
            status=attr("status"),
            market_indicator=attr("market_indicator"),
            code=attr("code"),
            has_bdr=attr("has_bdr"),
            type_bdr=attr("type_bdr"),
            has_quotation=attr("has_quotation"),
            has_emissions=attr("has_emissions"),
            date_quotation=attr("date_quotation"),
            last_date=attr("last_date"),
            listing_date=attr("listing_date"),
        )

    def to_dto(self) -> CompanyDataDTO:
        """Convert this model back into a :class:`CompanyDataDTO`.

        This method performs the inverse of ``from_dto``:
        it expands comma-separated strings into lists and parses the JSON
        representation of ``other_codes`` into :class:`CodeDTO` objects.

        Returns:
            CompanyDataDTO: DTO populated with values from this model,
            preserving the original structure expected by the domain layer.
        """

        # Expand tickers back from comma-separated string
        ticker_codes: List[str] = (
            self.ticker_codes.split(",") if self.ticker_codes else []
        )

        # Expand ISINs back from comma-separated string
        isin_codes: List[str] = self.isin_codes.split(",") if self.isin_codes else []

        # Parse JSON array of objects into a Python list
        raw_other = json.loads(self.other_codes) if self.other_codes else []

        # Rebuild CodeDTO entries from the fetched structure
        other_codes = [
            CodeDTO(code=item.get("code"), isin=item.get("isin")) for item in raw_other
        ]

        # Build the DTO with expanded collections and direct field transfers
        dto = CompanyDataDTO(
            cvm_code=self.cvm_code,
            issuing_company=self.issuing_company,
            trading_name=self.trading_name,
            company_name=self.company_name,
            cnpj=self.cnpj,
            ticker_codes=ticker_codes,
            isin_codes=isin_codes,
            other_codes=other_codes,
            industry_sector=self.industry_sector,
            industry_subsector=self.industry_subsector,
            industry_segment=self.industry_segment,
            industry_classification=self.industry_classification,
            industry_classification_eng=self.industry_classification_eng,
            activity=self.activity,
            company_segment=self.company_segment,
            company_segment_eng=self.company_segment_eng,
            company_category=self.company_category,
            company_type=self.company_type,
            listing_segment=self.listing_segment,
            registrar=self.registrar,
            website=self.website,
            institution_common=self.institution_common,
            institution_preferred=self.institution_preferred,
            market=self.market,
            status=self.status,
            market_indicator=self.market_indicator,
            code=self.code,
            has_bdr=self.has_bdr,
            type_bdr=self.type_bdr,
            has_quotation=self.has_quotation,
            has_emissions=self.has_emissions,
            date_quotation=self.date_quotation,
            last_date=self.last_date,
            listing_date=self.listing_date,
        )

        # Ensure the DTO carries the model id without mutating the original instance
        return dataclasses.replace(dto, id=self.id)
