from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional


class DataCleanerPort(ABC):
    """Interface for text, number and date normalization utilities."""

    @abstractmethod
    def clean_text(
        self, text: Optional[str], words_to_remove: Optional[List[str]] = None
    ) -> Optional[str]:
        """Return a cleaned text string."""
        raise NotImplementedError

    @abstractmethod
    def clean_number(self, text: str) -> Optional[float]:
        """Convert a string to ``float`` if possible."""
        raise NotImplementedError

    @abstractmethod
    def clean_date(self, text: Optional[str]) -> Optional[datetime]:
        """Parse a date string into ``datetime``."""
        raise NotImplementedError

    @abstractmethod
    def clean_dict_fields(
        self,
        entry: dict,
        text_keys: List[str],
        date_keys: List[str],
        number_keys: Optional[List[str]] = None,
    ) -> dict:
        """Clean multiple fields of ``entry`` in place."""
        raise NotImplementedError
