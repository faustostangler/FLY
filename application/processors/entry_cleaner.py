from __future__ import annotations

from typing import Dict, List, Optional, Type, Union

from domain.dtos.company_data_dto import (
    CompanyDataListingDTO,
    CompanyDataDetailDTO,
    CompanyDataDTO,
)
from infrastructure.adapters.datacleaner_adapter import DataCleanerPort


class EntryCleaner:
    """Convert raw listing entries into validated DTOs.

    This helper coordinates field normalization (text, dates, numbers)
    and then instantiates the target DTO type from the cleaned mapping.
    It keeps the cleaning concerns encapsulated and makes the transformation
    explicit and testable.
    """

    def __init__(self, data_cleaner: DataCleanerPort) -> None:
        """Initialize the cleaner with its data normalization dependency.

        Args:
            data_cleaner (DataCleaner): Component responsible for coercing and
                sanitizing dict fields (trimming text, parsing dates, and
                casting numeric values).
        """
        # Store the cleaning dependency for reuse across entries
        self.data_cleaner = data_cleaner

    def clean_entry(
        self,
        entry: Dict,
        text_keys: List[str],
        date_keys: List[str],
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
            date_keys (List[str]): Keys expected to be parsed as dates.
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
        cleaned = self.data_cleaner.clean_dict_fields(
            entry, text_keys, date_keys, number_keys
        )

        # Construct and return the typed DTO from the cleaned mapping
        return dto_class.from_dict(cleaned)
