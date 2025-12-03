"""Processors for cleaning and merging company data."""

from __future__ import annotations

import base64
import json
from typing import Dict, List, Optional, Type, Union, cast

from application import CompanyDataMapper
from domain.dto import CompanyDataDetailDTO, CompanyDataListingDTO, CompanyDataRawDTO
from domain.ports import LoggerPort
from infrastructure.helpers.datacleaner import DataCleaner
from infrastructure.http.affinity_port import AffinityHttpClient


class EntryCleaner:
    """Clean raw company listing entries."""

    def __init__(self, datacleaner: DataCleaner) -> None:
        """Initialize with ``DataCleaner``."""
        self.datacleaner = datacleaner

    def clean_entry(
        self,
        entry: Dict,
        text_keys: List[str],
        date_keys: List[str],
        number_keys: Optional[List[str]],
        dto_class: Type[Union[CompanyDataListingDTO, CompanyDataDetailDTO]],
    ) -> Union[CompanyDataListingDTO, CompanyDataDetailDTO]:
        """Return a ``CompanyDataListingDTO`` from the given entry."""
        cleaned = self.datacleaner.clean_dict_fields(
            entry, text_keys, date_keys, number_keys
        )
        return dto_class.from_dict(cleaned)


class DetailFetcher:
    """Fetch and clean detailed company information using an HTTP client."""

    def __init__(
        self,
        http_client: AffinityHttpClient,
        endpoint_detail: str,
        language: str,
    ) -> None:
        """Store HTTP client and configuration."""
        self.http_client = http_client
        self.endpoint_detail = endpoint_detail
        self.language = language

    def fetch_detail(self, session, cvm_code: str) -> Dict:
        """Fetch detail JSON and return the raw dict."""
        payload = {"codeCVM": cvm_code, "language": self.language}
        token = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")

        url = self.endpoint_detail + token
        body = self.http_client.fetch_with(session, url)
        raw = json.loads(body.decode("utf-8"))

        return raw


class CompanyDataMerger:
    """Merge base and detail DTOs."""

    def __init__(self, mapper: CompanyDataMapper, logger: LoggerPort) -> None:
        """Store mapper and logger."""
        self.mapper = mapper
        self.logger = logger

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def merge_details(
        self, listing: CompanyDataListingDTO, detail: CompanyDataDetailDTO
    ) -> Optional[CompanyDataRawDTO]:
        """Merge listing and detail DTOs into a raw DTO."""
        try:
            return self.mapper.merge_company_data_dtos(listing, detail)
        except Exception as exc:  # noqa: BLE001
            self.logger.log(f"erro {exc}", level="debug")
            return None


class CompanyDataDetailProcessor:
    """Pipeline to process a single company entry."""

    def __init__(
        self, cleaner: EntryCleaner, fetcher: DetailFetcher, merger: CompanyDataMerger
    ) -> None:
        """Store dependencies used to process a company entry."""
        self.cleaner = cleaner
        self.fetcher = fetcher
        self.merger = merger

    def process_entry(self, entry: Dict) -> Optional[CompanyDataRawDTO]:
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
