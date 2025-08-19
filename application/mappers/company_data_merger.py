from __future__ import annotations

from typing import Optional

from application.mappers.company_data_mapper import CompanyDataMapper
from domain.ports.config_port import ConfigPort
from domain.ports.logger_port import LoggerPort
from domain.dtos.company_data_dto import CompanyDataListingDTO, CompanyDataDetailDTO, CompanyDataDTO

class CompanyDataMerger:
    """Merge base and detail DTOs."""

    def __init__(self, mapper: CompanyDataMapper, logger: LoggerPort) -> None:
        """Store mapper and logger."""
        self.mapper = mapper
        self.logger = logger

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def merge_details(
        self, listing: CompanyDataListingDTO, detail: CompanyDataDetailDTO
    ) -> Optional[CompanyDataDTO]:
        """Merge listing and detail DTOs into a raw DTO."""
        try:
            return None # self.mapper.merge_company_data_dtos(listing, detail)
        except Exception as exc:  # noqa: BLE001
            self.logger.log(f"erro {exc}", level="debug")
            return None

