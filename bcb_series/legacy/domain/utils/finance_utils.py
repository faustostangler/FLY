"""Financial helper utilities."""

from __future__ import annotations


def safe_divide(numerator: float, denominator: float) -> float:
    """Return ``numerator`` divided by ``denominator`` or ``0.0`` when zero."""
    if denominator == 0:
        return 0.0
    return numerator / denominator
