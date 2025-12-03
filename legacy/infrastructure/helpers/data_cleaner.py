"""Helpers for applying normalization to raw company data."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Sequence, cast

from domain.ports import ConfigPort, LoggerPort
from domain.ports.datacleaner_port import DataCleanerPort
from infrastructure.utils.normalization import cleandate as util_cleandate
from infrastructure.utils.normalization import (
    clean_dict_fields as util_clean_dict_fields,
)
from infrastructure.utils.normalization import clean_number as util_clean_number
from infrastructure.utils.normalization import clean_text as util_clean_text

if TYPE_CHECKING:
    # Só para o type checker; evita import em runtime.
    from infrastructure.logging.logger import Logger as InfraLogger


class DataCleaner(DataCleanerPort):
    """Utility class for normalizing raw text, dates and numbers."""

    def __init__(self, config: ConfigPort, logger: LoggerPort) -> None:
        self.config = config
        self.logger = logger  # (typo corrigido)

    def clean_text(
        self,
        text: Optional[str],
        words_to_remove: Optional[Sequence[str]] = None,
    ) -> Optional[str]:
        words = list(words_to_remove or self.config.domain.words_to_remove or [])
        return util_clean_text(
            text,
            words_to_remove=words,
            logger=cast("InfraLogger", self.logger),
        )

    def clean_number(self, text: str) -> float:
        return util_clean_number(text, logger=cast("InfraLogger", self.logger))

    def cleandate(self, text: Optional[str]) -> Optional[datetime]:
        return util_cleandate(text, logger=cast("InfraLogger", self.logger))

    def clean_dict_fields(
        self,
        entry: dict,
        text_keys: List[str],
        date_keys: List[str],
        number_keys: Optional[List[str]] = None,
    ) -> dict:
        return util_clean_dict_fields(
            entry,
            text_keys,
            date_keys,
            number_keys,
            logger=cast("InfraLogger", self.logger),
            words_to_remove=list(self.config.domain.words_to_remove or []),
        )
