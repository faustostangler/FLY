"""Helpers for applying normalization to raw company data."""

from datetime import datetime
from typing import List, Optional

from domain.ports import ConfigPort
from domain.ports import LoggerPort
from domain.ports.data_cleaner_port import DataCleanerPort
from infrastructure.utils.normalization import (
    clean_date as util_clean_date,
)
from infrastructure.utils.normalization import (
    clean_dict_fields as util_clean_dict_fields,
)
from infrastructure.utils.normalization import (
    clean_number as util_clean_number,
)
from infrastructure.utils.normalization import (
    clean_text as util_clean_text,
)


class DataCleaner(DataCleanerPort):
    """Utility class for normalizing raw text, dates and numbers.

    Requires external configuration (e.g. words to remove) and a logger.
    """

    def __init__(self, config: ConfigPort, logger: LoggerPort) -> None:
        """Store configuration and logger."""
        self.config = config
        self.logger = logger

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def clean_text(
        self, text: Optional[str], words_to_remove: Optional[List[str]] = None
    ) -> Optional[str]:
        """Normalize a text string using ``utils.clean_text``."""
        words_to_remove = words_to_remove or self.config.domain.words_to_remove
        return util_clean_text(
            text, words_to_remove=words_to_remove, logger=self.logger
        )

    def clean_number(self, text: str) -> float:
        """Convert a stringified number using ``utils.clean_number``."""
        return util_clean_number(text, logger=self.logger)

    def clean_date(self, text: Optional[str]) -> Optional[datetime]:
        """Parse a date string using ``utils.clean_date``."""
        return util_clean_date(text, logger=self.logger)

    def clean_dict_fields(
        self,
        entry: dict,
        text_keys: List[str],
        date_keys: List[str],
        number_keys: Optional[List[str]] = None,
    ) -> dict:
        """Return a cleaned ``entry`` using ``utils.clean_dict_fields``."""

        return util_clean_dict_fields(
            entry,
            text_keys,
            date_keys,
            number_keys,
            logger=self.logger,
            words_to_remove=self.config.domain.words_to_remove,
        )
