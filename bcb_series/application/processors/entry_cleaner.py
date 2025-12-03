from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Type, Union, cast

from domain.dtos.company_data_dto import (
    CompanyDataDetailDTO,
    CompanyDataDTO,
    CompanyDataListingDTO,
)
from infrastructure.adapters.datacleaner_adapter import DataCleanerPort


class EntryCleaner:
    """Convert raw listing entries into validated DTOs.

    This helper coordinates field normalization (text, dates, numbers)
    and then instantiates the target DTO type from the cleaned mapping.
    It keeps the cleaning concerns encapsulated and makes the transformation
    explicit and testable.
    """

    def __init__(self, datacleaner: DataCleanerPort) -> None:
        """Initialize the cleaner with its data normalization dependency.

        Args:
            datacleaner (DataCleaner): Component responsible for coercing and
                sanitizing dict fields (trimming text, parsing dates, and
                casting numeric values).
        """
        # Store the cleaning dependency for reuse across entries
        self.datacleaner = datacleaner

    def clean_entry(
        self,
        entry: Dict,
        text_keys: List[str],
        date_keys: List[str],
        date_keys_norm: List[str],
        number_keys: Optional[List[str]],
        dto_class: Type[Union[CompanyDataListingDTO, CompanyDataDetailDTO]],
    ) -> Union[CompanyDataListingDTO, CompanyDataDetailDTO]:
        """Clean a raw entry and build a strongly-typed DTO instance.

        The method delegates normalization to ``DataCleaner`` and then calls
        ``from_dict`` on the provided DTO class to enforce schema and types.

        Args:
            entry (Dict): Raw entry with mixed field types and formats.
            text_keys (List[str]): Keys expected to be normalized as text
                (e.g., trimming, whitespace compaction).
            date_keys (List[str]): Keys expected to be fetched as dates.
            number_keys (Optional[List[str]]): Keys expected to be cast as
                numeric values. If ``None``, no numeric casting is attempted.
            dto_class (Type[Union[CompanyDataListingDTO, CompanyDataDetailDTO]]):
                Target DTO class whose ``from_dict`` will be used to instantiate
                the result.

        Returns:
            Union[CompanyDataListingDTO, CompanyDataDetailDTO]: A DTO instance
            populated from the cleaned mapping.

        Raises:
            ValueError: If the cleaned data does not satisfy the DTO schema.
            KeyError: If required keys are missing for the target DTO.
        """
        # Normalize raw fields into canonical text/date/number representations
        cleaned = self.datacleaner.clean_dict_fields(
            entry, text_keys, date_keys, date_keys_norm, number_keys
        )

        # Construct and return the typed DTO from the cleaned mapping
        if issubclass(dto_class, CompanyDataListingDTO):
            listing_class = cast(Type[CompanyDataListingDTO], dto_class)

            def _normalize_date(value: object) -> Optional[datetime]:
                if value is None:
                    return self.datacleaner.cleandate(None)
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    return self.datacleaner.cleandate(value)
                return self.datacleaner.cleandate(str(value))

            return listing_class.from_dict(cleaned, cleandate=_normalize_date)

        if issubclass(dto_class, CompanyDataDetailDTO):
            detail_class = cast(Type[CompanyDataDetailDTO], dto_class)
            return detail_class.from_dict(cleaned)

        raise TypeError(
            "Unsupported DTO class provided to EntryCleaner.clean_entry"
        )
