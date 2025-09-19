from __future__ import annotations

from domain.dto import (
    CompanyDataDetailDTO,
    CompanyDataListingDTO,
    CompanyDataRawDTO,
)
from domain.ports import DataCleanerPort


class CompanyDataMapper:
    """Merge base and detail company data into a parsed DTO."""

    def __init__(self, data_cleaner: DataCleanerPort) -> None:
        """Create a new mapper using the provided data cleaner utility."""
        self.data_cleaner = data_cleaner

    def merge_company_data_dtos(
        self,
        listing: CompanyDataListingDTO,
        detail: CompanyDataDetailDTO,
    ) -> CompanyDataRawDTO:
        """Combine listing and detail information into a single DTO."""
        # Extract the list of extra codes, falling back to an empty list.
        codes = detail.other_codes or []

        # Parse the industry classification string into separate segments.
        industry_classification = detail.industry_classification or ""
        parts = [p.strip() for p in industry_classification.split("/")]
        industry_sector = (
            self.data_cleaner.clean_text(parts[0]) if len(parts) > 0 else None
        )
        industry_subsector = (
            self.data_cleaner.clean_text(parts[1]) if len(parts) > 1 else None
        )
        industry_segment = (
            self.data_cleaner.clean_text(parts[2]) if len(parts) > 2 else None
        )

        # Build the raw company DTO with all collected information.
        return CompanyDataRawDTO(
            cvm_code=detail.cvm_code or listing.cvm_code,
            issuing_company=detail.issuing_company or listing.issuing_company,
            trading_name=detail.trading_name or listing.trading_name,
            company_name=detail.company_name or listing.company_name,
            cnpj=detail.cnpj or listing.cnpj,
            ticker_codes=[c.code for c in codes if c.code],
            isin_codes=[c.isin for c in codes if c.isin],
            other_codes=codes,
            industry_sector=industry_sector,
            industry_subsector=industry_subsector,
            industry_segment=industry_segment,
            industry_classification=industry_classification,
            industry_classification_eng=detail.industry_classification_eng or None,
            activity=detail.activity or None,
            company_segment=listing.segment or None,
            company_segment_eng=listing.segment_eng or None,
            company_category=detail.company_category or None,
            company_type=listing.company_type or None,
            listing_segment=detail.listing_segment or None,
            registrar=detail.registrar or None,
            website=detail.website or None,
            institution_common=detail.institution_common or None,
            institution_preferred=detail.institution_preferred or None,
            market=detail.market or listing.market,
            status=detail.status or listing.status,
            market_indicator=detail.market_indicator or listing.market_indicator,
            code=detail.code or None,
            has_bdr=detail.has_bdr or None,
            type_bdr=detail.type_bdr or listing.type_bdr,
            has_quotation=detail.has_quotation or None,
            has_emissions=detail.has_emissions or None,
            date_quotation=detail.date_quotation or None,
            last_date=detail.last_date,
            listing_date=listing.listing_date,
        )
