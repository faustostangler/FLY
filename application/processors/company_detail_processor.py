from __future__ import annotations

from typing import Dict, Optional, cast

from application.mappers.company_data_merger import CompanyDataMerger
from application.processors.entry_cleaner import EntryCleaner
from domain.dtos.company_data_dto import (
    CompanyDataDetailDTO,
    CompanyDataDTO,
    CompanyDataListingDTO,
)
from infrastructure.scrapers.scraper_company_detail import DetailFetcher


class CompanyDataDetailProcessor:
    """Process a single company record by cleaning, fetching details, and merging.

    This processor orchestrates three responsibilities:
      1) Normalize an incoming raw entry into a listing DTO.
      2) Fetch the company's detail payload from the remote source.
      3) Clean the detail payload and merge it with the listing into a single DTO.

    Dependencies are injected to keep the class testable and to separate concerns.

    Attributes:
        cleaner (EntryCleaner): Utility that normalizes raw dicts into typed DTOs.
        fetcher (DetailFetcher): Service that retrieves the company detail payload.
        merger (CompanyDataMerger): Component that merges listing and detail DTOs.
    """

    def __init__(
        self, cleaner: EntryCleaner, fetcher: DetailFetcher, merger: CompanyDataMerger
    ) -> None:
        """Initialize the processor with its collaborators.

        Args:
            cleaner (EntryCleaner): Normalizes and validates input mappings.
            fetcher (DetailFetcher): Performs the HTTP call to get detail data.
            merger (CompanyDataMerger): Combines listing and detail into the output DTO.
        """
        # Store the cleaning utility for normalizing inputs into DTOs
        self.cleaner = cleaner

        # Store the detail fetcher responsible for external calls
        self.fetcher = fetcher

        # Store the merger that composes the final DTO
        self.merger = merger

    def process_entry(self, entry: Dict) -> Optional[CompanyDataDTO]:
        """Process a raw company entry end-to-end.

        Steps:
            1. Clean and coerce the input mapping into a `CompanyDataListingDTO`.
            2. Fetch the detail payload using the listing's `cvm_code`.
            3. Clean the detail mapping into a `CompanyDataDetailDTO`.
            4. Merge listing and detail into a `CompanyDataDTO`.

        Args:
            entry (Dict): Raw mapping representing a company row.

        Returns:
            Optional[CompanyDataDTO]: Merged DTO on success; `None` if processing fails.

        Notes:
            Any exception is intentionally swallowed (by design here) and results in `None`.
            Consider adding structured logging/metrics around failures in production.
        """
        try:
            # Define which text fields should be normalized for the listing DTO
            text_keys = [
                "issuingCompany",
                "companyName",
                "tradingName",
                "segment",
                "segmentEng",
                "market",
            ]

            # Define date fields for the listing DTO
            date_keys = ["dateListing"]
            date_keys_norm = []

            # No numeric fields expected for the listing DTO
            number_keys = []

            # Clean and coerce the input mapping into a strongly-typed listing DTO
            listing = cast(
                CompanyDataListingDTO,
                self.cleaner.clean_entry(
                    entry=entry,
                    text_keys=text_keys,
                    date_keys=date_keys,
                    date_keys_norm=date_keys_norm,
                    number_keys=number_keys,
                    dto_class=CompanyDataListingDTO,
                ),
            )

            # Borrow a shared HTTP session to perform the detail request efficiently
            with self.fetcher.http_client.borrow_session() as session:
                # Fetch the detailed payload keyed by the company's CVM code
                detail = self.fetcher.fetch_detail(session, str(listing.cvm_code))

            # Define which text fields should be normalized for the detail DTO
            # Note: "market" appears twice and "institutionPreffered" seems misspelled.
            # This mirrors the source payload as-is; adjust upstream if needed.
            text_keys = [
                "issuingCompany",
                "companyName",
                "tradingName",
                "IndustryClassificationEng",
                "market",
                "institutionCommon",
                "institutionPreferred",
                "market",
                "institutionCommon",
                "institutionPreffered",
            ]

            # Define date fields present in the detail payload
            date_keys = ["lastDate", "dateQuotation"]
            date_keys_norm = []

            # No numeric fields expected for the detail DTO
            number_keys = []

            # Clean and coerce the detail mapping into a strongly-typed detail DTO
            detail = cast(
                CompanyDataDetailDTO,
                self.cleaner.clean_entry(
                    entry=detail,
                    text_keys=text_keys,
                    date_keys=date_keys,
                    date_keys_norm=date_keys_norm,
                    number_keys=number_keys,
                    dto_class=CompanyDataDetailDTO,
                ),
            )

            # Merge listing and detail into the final unified DTO
            return self.merger.merge_details(listing, detail)

        except Exception as e:  # noqa: F841
            # Intentionally swallow exceptions to keep the pipeline resilient;
            # consider instrumenting logging or metrics for observability.
            pass
