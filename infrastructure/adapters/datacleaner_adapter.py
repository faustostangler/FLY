from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Iterable, Mapping, Optional, cast

import infrastructure.utils.normalization as norm
from domain.ports.config_port import ConfigPort
from domain.ports.datacleaner_port import DataCleanerPort
from domain.ports.logger_port import LoggerPort

if TYPE_CHECKING:
    from infrastructure.logging.logger_adapter import Logger


class DataCleaner(DataCleanerPort):
    """Utility class for normalizing raw text, dates and numbers."""

    def __init__(self, config: ConfigPort, logger: LoggerPort) -> None:
        self.config = config
        self.logger = logger

    def clean_text(
        self,
        text: Optional[str],
        words_to_remove: Optional[Iterable[str]] = None,
    ) -> Optional[str]:
        words = list(words_to_remove or self.config.domain.words_to_remove or [])
        return norm.clean_text(
            text,
            words_to_remove=words,
            logger=cast("Logger", self.logger),
        )

    def clean_number(self, text: str) -> float:
        return norm.clean_number(text, logger=cast("Logger", self.logger))

    def clean_date(self, text: Optional[str]) -> Optional[datetime]:
        return norm.clean_date(text, logger=cast("Logger", self.logger))

    def clean_dict_fields(
        self,
        entry: Mapping[str, object],
        text_keys: Optional[Iterable[str]],
        date_keys: Optional[Iterable[str]],
        number_keys: Optional[Iterable[str]] = None,
    ) -> dict:
        return norm.clean_dict_fields(
            entry=entry,
            text_keys=text_keys or [],
            date_keys=date_keys or [],
            number_keys=number_keys or [],
            logger=cast("Logger", self.logger),
            words_to_remove=list(self.config.domain.words_to_remove or []),
        )

