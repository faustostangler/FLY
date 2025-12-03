from __future__ import annotations

from typing import Optional

from application.mappers.company_data_mapper import CompanyDataMapper

# from domain.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.dtos.company_data_dto import (
    CompanyDataDetailDTO,
    CompanyDataDTO,
    CompanyDataListingDTO,
)


class CompanyDataMerger:
    """Coordinates the merge of listing and detail company DTOs.

    This class encapsulates the mapping step that combines a lightweight
    listing DTO with a detailed DTO into a unified `CompanyDataDTO`.

    Args:
        mapper (CompanyDataMapper): Component responsible for transforming and
            merging DTOs into a single domain object.
        logger (LoggerPort): Logging port used for diagnostics and error tracing.
    """

    def __init__(self, mapper: CompanyDataMapper, logger: LoggerPort) -> None:
        """Initialize the merger with its collaborators.

        Stores references to the mapper and logger for later use.

        Args:
            mapper (CompanyDataMapper): DTO merge/transform utility.
            logger (LoggerPort): Logger implementation for observability.
        """
        # Keep the mapper used to merge listing and detail DTOs
        self.mapper = mapper

        # Keep the logger for operational and error logs
        self.logger = logger

        # Optional lifecycle log for class loading; disabled to avoid noise
        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def merge_details(
        self, listing: CompanyDataListingDTO, detail: CompanyDataDetailDTO
    ) -> Optional[CompanyDataDTO]:
        """Merge a listing DTO with its corresponding detail DTO.

        Delegates the actual merge operation to the injected mapper and
        returns a single consolidated `CompanyDataDTO`. On failure, logs
        the exception and returns `None`.

        Args:
            listing (CompanyDataListingDTO): Lightweight company overview data.
            detail (CompanyDataDetailDTO): Detailed company attributes that
                complement the listing.

        Returns:
            Optional[CompanyDataDTO]: The merged domain DTO if the operation
            succeeds; otherwise, `None`.

        Raises:
            None: Any exceptions are caught and logged; the method degrades
            gracefully by returning `None`.
        """
        # Attempt to perform the merge using the mapper
        try:
            # Return the merged DTO when the mapper is enabled
            return self.mapper.create_company_data_dto(listing, detail)
        except Exception as exc:  # noqa: BLE001
            # Log the error for troubleshooting and return a safe fallback
            self.logger.log(f"erro {exc}", level="debug")
            return None
