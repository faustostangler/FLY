from __future__ import annotations

from domain.dtos.company_data_dto import (
    CompanyDataDetailDTO,
    CompanyDataDTO,
    CompanyDataListingDTO,
)
from domain.ports.datacleaner_port import DataCleanerPort


class CompanyDataMapper:
    """Mapper that merges company listing and detail data into a fetched DTO."""

    def __init__(self, datacleaner: DataCleanerPort) -> None:
        """Initialize the mapper with a data cleaning utility.

        Args:
            datacleaner (DataCleanerPort): Utility responsible for cleaning
                free-text fields before mapping into DTOs.
        """
        self.datacleaner = datacleaner

    def create_company_data_dto(
        self,
        listing: CompanyDataListingDTO,
        detail: CompanyDataDetailDTO,
    ) -> CompanyDataDTO:
        """Build a unified company DTO from listing and detail information.

        Args:
            listing (CompanyDataListingDTO): Basic listing data about the company.
            detail (CompanyDataDetailDTO): Detailed data about the company.

        Returns:
            CompanyDataDTO: Fully populated data transfer object combining
            both listing and detail sources.
        """
        # Collect any extra codes provided in the detail object
        codes = detail.other_codes or []

        # Extract and normalize the industry classification hierarchy
        industry_classification = detail.industry_classification or ""
        parts = [p.strip() for p in industry_classification.split("/")]

        # Map each classification level safely, cleaning the text if present
        industry_sector = (
            self.datacleaner.clean_text(parts[0]) if len(parts) > 0 else None
        )
        industry_subsector = (
            self.datacleaner.clean_text(parts[1]) if len(parts) > 1 else None
        )
        industry_segment = (
            self.datacleaner.clean_text(parts[2]) if len(parts) > 2 else None
        )

        # Construct and return the aggregated company DTO
        return CompanyDataDTO(
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
