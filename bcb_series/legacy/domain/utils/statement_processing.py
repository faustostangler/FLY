from __future__ import annotations

"""Utility helpers for statement parsing."""


def classify_section(label: str) -> str:
    """Classify a row label into a section name."""
    text = label.lower()
    if "asset" in text:
        return "ASSET"
    if "liability" in text:
        return "LIABILITY"
    return "UNKNOWN"


def normalize_value(raw: str) -> float:
    """Convert a numeric string into a float."""
    cleaned = raw.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
