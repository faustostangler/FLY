from __future__ import annotations

import re
import string
from datetime import datetime
from typing import Dict, List, Mapping, Optional

import unidecode

from application.ports.logger_port import LoggerPort


def clean_text(
    text: Optional[str],
    words_to_remove: Optional[List[str]] = None,
    logger: Optional[LoggerPort] = None,
) -> Optional[str]:
    """Normalize a free-form text string.

    This helper standardizes text to simplify downstream matching and comparisons.
    It removes diacritics, strips punctuation, uppercases the text, collapses
    whitespace, and optionally removes specific whole words.

    Args:
        text: Input string to normalize. If falsy (e.g., ``None`` or empty), returns ``None``.
        words_to_remove: Optional iterable of words to be removed as whole words (word boundaries).
        logger: Optional logger interface used to record non-fatal cleaning issues.

    Returns:
        The normalized string, or ``None`` when the input is empty/None or an error occurs.

    Notes:
        - Word removal uses a single compiled alternation pattern with word boundaries.
        - All punctuation characters found in :mod:`string.punctuation` are stripped.
    """
    # Guard transformation steps to keep failures non-fatal and traceable
    try:
        # Short-circuit on falsy values to avoid returning empty strings downstream
        if not text:
            return None

        # Remove diacritics to ASCII to normalize accents (e.g., "ação" -> "acao")
        text = unidecode.unidecode(text)

        # Strip punctuation to reduce token variability
        text = text.translate(str.maketrans("", "", string.punctuation))

        # Normalize case and trim outer spaces for consistent comparisons
        text = text.upper().strip()

        # Collapse any internal runs of whitespace into a single space
        text = re.sub(r"\s+", " ", text)

        # Optionally remove a curated set of whole words before returning
        if words_to_remove:
            # Build a safe alternation pattern using escaped literals with word boundaries
            pattern = r"\b(?:" + "|".join(map(re.escape, words_to_remove)) + r")\b"

            # Drop matched words and re-collapse whitespace after removal
            text = re.sub(pattern, "", text)
            text = re.sub(r"\s+", " ", text).strip()

        # Return the fully normalized value
        return text
    except Exception as exc:  # noqa: BLE001
        # Best-effort logging while keeping the pipeline resilient
        if logger:
            logger.log(f"Failed to clean text: {exc}", level="warning")
        return None

# Accepts None, str, int, float; returns a best-effort float normalization
def clean_number(
    text: Optional[object],
    logger: Optional[LoggerPort] = None,
) -> float:
    """Convert diverse textual/primitive inputs into a ``float``.

    This function is tolerant of common numeric formats and whitespace noise.
    It handles integers/floats directly, converts strings with thousand/decimal
    separators, and defaults to ``0.0`` on invalid or empty inputs.

    Args:
        text: Input value to coerce (e.g., ``None``, ``str``, ``int``, ``float``).
        logger: Optional logger interface for warnings on parse failures.

    Returns:
        A floating-point value representing the fetched input, or ``0.0`` on failure.

    Notes:
        - Dots (``.``) are treated as thousands separators and removed.
        - Commas (`,`) are treated as decimal separators and converted to dots
          prior to ``float`` conversion.
    """
    # Guard transformation steps to keep failures non-fatal and traceable
    try:
        # Map None directly to 0.0 for predictable downstream numeric operations
        if text is None:
            return 0.0

        # Fast-path for already numeric inputs while enforcing float type
        if isinstance(text, (int, float)):
            return float(text)

        # Coerce any other type to string for canonical parsing
        s = str(text)
        if not s:
            return 0.0

        # Remove whitespace/control chars and normalize separators
        s = re.sub(r"[\s\r\n\t]+", "", s)
        s = s.replace(".", "").replace(",", ".")

        # Best-effort float parsing after normalization
        return float(s)
    except Exception as exc:  # noqa: BLE001
        # Log and degrade gracefully to 0.0 to avoid caller exceptions
        if logger:
            logger.log(f"Failed to clean number: {exc}", level="warning")
        return 0.0

def cleandate(
    text: Optional[str],
    normalization: Optional[bool] = False,
    logger: Optional[LoggerPort] = None,
) -> Optional[datetime]:
    """Parse a date-like value into ``datetime``.

    Attempts a small set of common date/time formats. Returns the original value
    untouched if it is already a :class:`datetime.datetime`. Otherwise, returns
    ``None`` when the input is empty or no format matches.

    Args:
        text: Input string representing a date/time.
        logger: Optional logger used to trace unsupported formats.

    Returns:
        A ``datetime`` instance when parsing succeeds; otherwise ``None``.

    NsdTypePolicy Formats:
        - ``%d/%m/%Y %H:%M:%S`` (e.g., 31/12/2024 23:59:59)
        - ``%m/%d/%Y %H:%M:%S``
        - ``%Y-%m-%d %H:%M:%S``
        - ``%d/%m/%Y``
        - ``%m/%d/%Y``
        - ``%Y-%m-%d``
    """
    # If already a datetime, return as-is to avoid unnecessary parsing work
    if isinstance(text, datetime):
        return text

    # Empty inputs are treated as missing values
    if not text:
        return None

    # Try a curated set of formats from most to least specific
    patterns = [
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%d",
    ]

    # Iterate through formats to find the first successful parse
    for fmt in patterns:
        try:
            dt = datetime.strptime(text.strip(), fmt)

            # Find end of quarter
            if normalization:
                q = (dt.month - 1) // 3 + 1
                if q == 1:
                    dt = datetime(dt.year, 3, 31)
                elif q == 2:
                    dt = datetime(dt.year, 6, 30)
                elif q == 3:
                    dt = datetime(dt.year, 9, 30)
                else:
                    dt = datetime(dt.year, 12, 31)
            return dt

        except Exception:
            # Keep trying other formats without failing fast
            continue

    # Provide debug-level trace when no patterns match
    if logger:
        logger.log(f"Failed to parse date: unsupported format '{text}'", level="debug")
    return None

def clean_dict_fields(
    entry: Mapping[str, object],
    text_keys: List[str],
    date_keys: List[str],
    date_keys_norm: Optional[List[str]] = None,
    number_keys: Optional[List[str]] = None,
    *,
    logger,
    words_to_remove: Optional[List[str]] = None,
) -> Dict:
    """Produce a cleaned copy of a mapping, normalizing select fields.

    Applies field-wise normalization on a shallow copy of ``entry``:
    - Text keys are normalized via :func:`clean_text`.
    - Date keys are fetched via :func:`cleandate`.
    - Number keys are coerced via :func:`clean_number`.

    Args:
        entry: Original mapping that contains raw values.
        text_keys: Keys in ``entry`` to be normalized as text.
        date_keys: Keys in ``entry`` to be fetched as dates.
        number_keys: Optional keys to be coerced to floats. Defaults to empty.
        logger: Required logger interface used by the underlying cleaning functions.
        words_to_remove: Optional list of stop-words to drop from text fields.

    Returns:
        A new ``dict`` containing the normalized values for the specified keys,
        leaving other keys untouched.

    Notes:
        - This function is intentionally shallow; it does not traverse nested structures.
        - Missing keys are ignored silently to keep the operation idempotent on partial inputs.
    """
    # Use an empty list to simplify iteration logic when number_keys is not provided
    number_keys = number_keys or []

    # Work on a shallow copy to keep the original mapping unmodified
    cleaned = dict(entry)

    # Normalize configured text fields
    for key in text_keys or []:
        if key in cleaned:
            # Guard type: only strings are text-normalized; others become None
            val = entry.get(key)
            cleaned[key] = clean_text(
                text=val if isinstance(val, str) else None,
                words_to_remove=words_to_remove,
                logger=logger,
            )

    # Parse configured date fields
    for key in date_keys or []:
        if key in cleaned:
            # Guard type: only strings are fetched; others become None
            val = entry.get(key)
            cleaned[key] = cleandate(
                text=val if isinstance(val, str) else None,
                normalization=False,
                logger=logger,
            )

    for key in date_keys_norm or []:
        if key in cleaned:
            # Guard type: only strings are fetched; others become None
            val = entry.get(key)
            cleaned[key] = cleandate(
                text=val if isinstance(val, str) else None,
                normalization=True,
                logger=logger,
            )

    # Coerce configured numeric fields
    for key in number_keys or []:
        if key in cleaned:
            val = entry.get(key)
            cleaned[key] = clean_number(val, logger=logger)

    # Return the normalized mapping
    return cleaned
