from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Mapping, Optional, cast

import infrastructure.utils.normalization as norm
from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from domain.ports.datacleaner_port import DataCleanerPort

if TYPE_CHECKING:
    from infrastructure.logging.logger_adapter import Logger


class DataCleaner(DataCleanerPort):
    """Utility class for normalizing raw text, dates, and numbers.

    Provides a consistent interface to clean text, numbers, and dates
    using project-defined normalization utilities.
    """

    def __init__(self, config: ConfigPort, logger: LoggerPort) -> None:
        """Initialize the DataCleaner with configuration and logger.

        Args:
            config (ConfigPort): Provides domain-specific cleaning rules,
                such as words to remove.
            logger (LoggerPort): Logger interface for reporting issues
                during data cleaning.
        """
        # Configuration source with cleaning rules
        self.config = config

        # Logging interface used by normalization functions
        self.logger = logger

    def clean_text(
        self,
        text: Optional[str],
        words_to_remove: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Normalize and clean text by removing unwanted words.

        Args:
            text (Optional[str]): Input string to be cleaned.
            words_to_remove (Optional[List[str]]): Custom words to remove.
                If not provided, defaults to words from configuration.

        Returns:
            Optional[str]: Cleaned and normalized text, or None if input is None.
        """
        # Build the effective list of words to remove
        words = list(words_to_remove or self.config.domain.words_to_remove or [])

        # Delegate to normalization utility
        return norm.clean_text(
            text,
            words_to_remove=words,
            logger=cast("Logger", self.logger),
        )

    def clean_number(self, text: str) -> float:
        """Normalize numeric strings into float values.

        Args:
            text (str): Input string representing a number.

        Returns:
            float: Fetched and cleaned numeric value.
        """
        return norm.clean_number(text, logger=cast("Logger", self.logger))

    def cleandate(self, text: Optional[str]) -> Optional[datetime]:
        """Parse and normalize a date string.

        Args:
            text (Optional[str]): Input string representing a date.

        Returns:
            Optional[datetime]: Fetched datetime object, or None if invalid.
        """
        return norm.cleandate(text, logger=cast("Logger", self.logger))

    def clean_dict_fields(
        self,
        entry: Mapping[str, object],
        text_keys: Optional[List[str]],
        date_keys: Optional[List[str]],
        date_keys_norm: Optional[List[str]],
        number_keys: Optional[List[str]] = None,
    ) -> dict:
        """Clean multiple fields of a dictionary according to their types.

        Args:
            entry (Mapping[str, object]): Input dictionary with raw values.
            text_keys (Optional[List[str]]): Keys whose values should be cleaned as text.
            date_keys (Optional[List[str]]): Keys whose values should be fetched as dates.
            number_keys (Optional[List[str]]): Keys whose values should be fetched as numbers.

        Returns:
            dict: A new dictionary with cleaned values.
        """
        return norm.clean_dict_fields(
            entry=entry,
            text_keys=text_keys or [],
            date_keys=date_keys or [],
            date_keys_norm=date_keys_norm or [],
            number_keys=number_keys or [],
            logger=cast("Logger", self.logger),
            words_to_remove=list(self.config.domain.words_to_remove or []),
        )
