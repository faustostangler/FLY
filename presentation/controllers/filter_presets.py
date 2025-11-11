from __future__ import annotations

from typing import Any, Dict

FilterDict = Dict[str, Any]


def build_ratios_filter_by_issuing_company(issuing_company: str) -> FilterDict:
    """Return a basic filter selecting ratios by the issuing company name."""

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
    """Return the default ratios filter tree placeholder."""

    return {}
