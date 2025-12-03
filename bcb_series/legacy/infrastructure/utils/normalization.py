"""Utility functions for cleaning and normalizing raw text."""

from __future__ import annotations

import re
import string
from datetime import datetime
from typing import Dict, List, Optional

import unidecode

from infrastructure.logging import Logger


def clean_text(
    text: Optional[str],
    words_to_remove: Optional[List[str]] = None,
    logger: Optional[Logger] = None,
) -> Optional[str]:
    """Normalize a text string.

    Remove punctuation, accents and stop words.
    """
    try:
        if not text:
            return None

        text = unidecode.unidecode(text)
        text = text.translate(str.maketrans("", "", string.punctuation))
        text = text.upper().strip()
        text = re.sub(r"\s+", " ", text)

        if words_to_remove:
            pattern = r"\b(?:" + "|".join(map(re.escape, words_to_remove)) + r")\b"
            text = re.sub(pattern, "", text)
            text = re.sub(r"\s+", " ", text).strip()

        return text
    except Exception as exc:  # noqa: BLE001
        if logger:
            logger.log(f"Failed to clean text: {exc}", level="warning")
        return None


def clean_number(
    text: Optional[object],  # aceita None, str, int, float
    logger: Optional[Logger] = None,
) -> float:
    """Convert diverse textual/primitive inputs into ``float``."""
    try:
        # None ou string vazia → 0.0
        if text is None:
            return 0.0

        # Já numérico → normaliza para float
        if isinstance(text, (int, float)):
            return float(text)

        # Qualquer outro tipo vira string
        s = str(text)
        if not s:
            return 0.0

        # Remove \r, \n, \t, espaços; normaliza separadores
        s = re.sub(r"[\s\r\n\t]+", "", s)
        s = s.replace(".", "").replace(",", ".")

        return float(s)
    except Exception as exc:  # noqa: BLE001
        if logger:
            logger.log(f"Failed to clean number: {exc}", level="warning")
        return 0.0


def cleandate(
    text: Optional[str],
    logger: Optional[Logger] = None,
) -> Optional[datetime]:
    """Attempt to parse a date string using common formats."""
    if isinstance(text, datetime):
        return text

    if not text:
        return None

    patterns = [
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%d",
    ]
    for fmt in patterns:
        try:
            return datetime.strptime(text.strip(), fmt)
        except Exception:
            continue

    if logger:
        logger.log(f"Failed to parse date: unsupported format '{text}'", level="debug")
    return None


def clean_dict_fields(
    entry: Dict,
    text_keys: List[str],
    date_keys: List[str],
    number_keys: Optional[List[str]] = None,
    *,
    logger: Optional[Logger] = None,
    words_to_remove: Optional[List[str]] = None,
) -> Dict:
    """Return a cleaned copy of ``entry``.

    Normalize its text, date and number fields.
    """
    number_keys = number_keys or []
    cleaned = entry.copy()

    for key in text_keys:
        if key in cleaned:
            cleaned[key] = clean_text(cleaned.get(key), words_to_remove, logger)

    for key in date_keys:
        if key in cleaned:
            cleaned[key] = cleandate(cleaned.get(key), logger)

    for key in number_keys:
        if key in cleaned:
            cleaned[key] = clean_number(cleaned.get(key), logger)

    return cleaned
