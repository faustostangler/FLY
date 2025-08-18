from __future__ import annotations

from datetime import datetime
from typing import Iterable, Mapping, Optional, Protocol, runtime_checkable


@runtime_checkable
class DataCleanerPort(Protocol):
    """Contract for text, number and date normalization utilities."""

    def clean_text(
        self,
        text: Optional[str],
        words_to_remove: Optional[Iterable[str]] = None,
    ) -> Optional[str]:
        ...

    def clean_number(self, text: str) -> Optional[float]:
        ...

    def clean_date(self, text: Optional[str]) -> Optional[datetime]:
        ...

    def clean_dict_fields(
        self,
        entry: Mapping[str, object],
        text_keys: Optional[Iterable[str]],
        date_keys: Optional[Iterable[str]],
        number_keys: Optional[Iterable[str]] = None,
    ) -> dict:
        """Return a NEW dict with cleaned fields; do not mutate the input."""
        ...
