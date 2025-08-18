from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Sequence, cast

from domain.ports import LoggerPort
from infrastructure.utils.normalization import (
    clean_date,
    clean_dict_fields,
    clean_number,
    clean_text,
)

if TYPE_CHECKING:
    from infrastructure.config.config_adapter import ConfigAdapter
    from infrastructure.logging.logger_adapter import Logger


class DataCleaner():
    """Utility class for normalizing raw text, dates and numbers."""

    def __init__(self, config: ConfigAdapter, logger: LoggerPort) -> None:
        self.config = config
        self.logger = logger  # (typo corrigido)

    def dataclean_text(
        self,
        text: Optional[str],
        words_to_remove: Optional[Sequence[str]] = None,
    ) -> Optional[str]:
        words = list(words_to_remove or self.config.domain.words_to_remove or [])
        return clean_text(
            text,
            words_to_remove=words,
            logger=cast("Logger", self.logger),
        )

    def dataclean_number(self, text: str) -> float:
        return clean_number(text, logger=cast("Logger", self.logger))

    def dataclean_date(self, text: Optional[str]) -> Optional[datetime]:
        return clean_date(text, logger=cast("Logger", self.logger))

    def dataclean_dict_fields(
        self,
        entry: dict,
        text_keys: List[str],
        date_keys: List[str],
        number_keys: Optional[List[str]] = None,
    ) -> dict:
        return clean_dict_fields(
            entry,
            text_keys,
            date_keys,
            number_keys,
            logger=cast("Logger", self.logger),
            words_to_remove=list(self.config.domain.words_to_remove or []),
        )


def datacleaner_factory(config: ConfigAdapter, logger: LoggerPort) -> DataCleaner:
    """Factory that builds a ready-to-use ``DataCleaner`` instance."""
    return DataCleaner(config, logger)

