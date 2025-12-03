from __future__ import annotations

from datetime import datetime
from typing import List, Mapping, Optional, Protocol, runtime_checkable


@runtime_checkable
class DataCleanerPort(Protocol):
    """Normalization utilities contract for text, numbers, and dates.

    This protocol defines the surface required by components that clean
    unstructured inputs before storage or business-rule validation.

    Implementations should be pure (no side effects) and avoid mutating inputs.
    """

    def clean_text(
        self,
        text: Optional[str],
        words_to_remove: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Normalize free-text content.

        Implementations typically trim whitespace, collapse internal spaces,
        unify casing when appropriate, and optionally remove provided stopwords.

        Args:
            text: Raw text or ``None``.
            words_to_remove: Iterable of words/phrases to strip from ``text``;
                matching strategy is implementation-defined.

        Returns:
            The cleaned text, or ``None`` if the input is empty/invalid after cleaning.
        """
        ...

    def clean_number(self, text: str) -> Optional[float]:
        """Parse and normalize a numeric value from text.

        Implementations may handle locale-specific separators, currency symbols,
        and tolerate minor noise (e.g., commas, spaces).

        Args:
            text: Raw textual representation of a number.

        Returns:
            A fetched ``float`` if conversion succeeds; otherwise ``None``.
        """
        ...

    def cleandate(self, text: Optional[str]) -> Optional[datetime]:
        """Parse and normalize a date/time from text.

        Implementations should accept common date formats, handle timezone
        hints if present, and return a timezone-naive or aware ``datetime``
        consistently per implementation policy.

        Args:
            text: Raw date string or ``None``.

        Returns:
            A ``datetime`` instance on success; otherwise ``None``.
        """
        ...

    def clean_dict_fields(
        self,
        entry: Mapping[str, object],
        text_keys: Optional[List[str]],
        date_keys: Optional[List[str]],
        date_keys_norm: Optional[List[str]],
        number_keys: Optional[List[str]] = None,
    ) -> dict:
        """Return a new mapping with selected fields cleaned.

        The input mapping must not be mutated; implementations should copy
        and transform only the specified keys using the corresponding cleaners.

        Args:
            entry: Source mapping containing raw values.
            text_keys: Keys whose values should be normalized as text.
            date_keys: Keys whose values should be fetched as dates.
            number_keys: Keys whose values should be fetched as numbers.

        Returns:
            A new ``dict`` with cleaned values and untouched unspecified fields.
        """
        ...
