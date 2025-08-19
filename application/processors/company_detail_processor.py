from __future__ import annotations

from typing import Dict, Optional, cast

from domain.dtos.company_data_dto import CompanyDataListingDTO, CompanyDataDetailDTO, CompanyDataDTO
from application.mappers.company_data_merger import CompanyDataMerger
from infrastructure.scrapers.company_detail_scraper import DetailFetcher
from application.processors.entry_cleaner import EntryCleaner

class CompanyDataDetailProcessor:
    """Pipeline to process a single company entry."""

    def __init__(
        self, cleaner: EntryCleaner, fetcher: DetailFetcher, merger: CompanyDataMerger
    ) -> None:
        """Store dependencies used to process a company entry."""
        self.cleaner = cleaner
        self.fetcher = fetcher
        self.merger = merger

    def process_entry(self, entry: Dict) -> Optional[CompanyDataDTO]:
        """Clean, fetch details, and merge into a raw DTO."""
        try:
            text_keys = [
                "issuingCompany",
                "companyName",
                "tradingName",
                "segment",
                "segmentEng",
                "market",
            ]
            date_keys = ["dateListing"]
            number_keys = []
            listing = cast(
                CompanyDataListingDTO,
                self.cleaner.clean_entry(
                    entry=entry,
                    text_keys=text_keys,
                    date_keys=date_keys,
                    number_keys=number_keys,
                    dto_class=CompanyDataListingDTO,
                ),
            )

            with self.fetcher.http_client.borrow_session() as session:
                detail = self.fetcher.fetch_detail(session, str(listing.cvm_code))
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
            date_keys = ["lastDate", "dateQuotation"]
            number_keys = []
            detail = cast(
                CompanyDataDetailDTO,
                self.cleaner.clean_entry(
                    entry=detail,
                    text_keys=text_keys,
                    date_keys=date_keys,
                    number_keys=number_keys,
                    dto_class=CompanyDataDetailDTO,
                ),
            )

            return self.merger.merge_details(listing, detail)
        except Exception as e:  # noqa: F841
            # print(e)
            pass
