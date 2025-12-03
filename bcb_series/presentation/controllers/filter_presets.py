"""Utilities that centralise reusable filter trees for CLI and adapters."""

from __future__ import annotations

from typing import Any, Dict


FilterDict = Dict[str, Any]


def build_ratios_filter_by_issuing_company(issuing_company: str) -> FilterDict:
    """Return a simple tree filtering companies by ``issuing_company``.

    The structure aligns with :class:`SearchFilterTree` and ``FilterBuilder``,
    making it safe to reuse in CLI automation and HTTP adapters.
    """

    company = (issuing_company or "").strip()
    if not company:
        raise ValueError("issuing_company must be a non-empty string")

    return {
        "and": [
            {
                "issuing_company": {
                    "==": company,
                    "case": False,
                }
            }
        ]
    }


def build_default_ratios_filter() -> FilterDict:
    """Return the default tree used when no custom filter is provided."""

    return {}


__all__ = [
    "build_default_ratios_filter",
    "build_ratios_filter_by_issuing_company",
]

