from __future__ import annotations

from typing import Dict, List, Optional, Type, Union

from domain.dtos.company_data_dto import CompanyDataListingDTO, CompanyDataDetailDTO, CompanyDataDTO
from infrastructure.adapters.datacleaner_adapter import DataCleaner

class EntryCleaner:
    """Clean raw company listing entries."""

    def __init__(self, data_cleaner: DataCleaner) -> None:
        """Initialize with ``DataCleaner``."""
        self.data_cleaner = data_cleaner

    def clean_entry(
        self,
        entry: Dict,
        text_keys: List[str],
        date_keys: List[str],
        number_keys: Optional[List[str]],
        dto_class: Type[Union[CompanyDataListingDTO, CompanyDataDetailDTO]],
    ) -> Union[CompanyDataListingDTO, CompanyDataDetailDTO]:
        """Return a ``CompanyDataListingDTO`` from the given entry."""
        cleaned = self.data_cleaner.clean_dict_fields(
            entry, text_keys, date_keys, number_keys
        )
        return dto_class.from_dict(cleaned)

