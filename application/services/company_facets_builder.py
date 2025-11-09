"""Utilities for building company facet buckets from search results."""

from __future__ import annotations

from typing import Dict, Iterable, List

from domain.dtos.company_eligible_dto import CompanyEligibleDTO
from domain.value_objects.company_filters import CompanyField


STRING_FIELDS: tuple[CompanyField, ...] = (
    CompanyField.ISSUING_COMPANY,
    CompanyField.TRADING_NAME,
    CompanyField.COMPANY_NAME,
    CompanyField.CNPJ,
    CompanyField.MARKET,
    CompanyField.INDUSTRY_SECTOR,
    CompanyField.INDUSTRY_SUBSECTOR,
    CompanyField.INDUSTRY_SEGMENT,
    CompanyField.INDUSTRY_CLASSIFICATION,
    CompanyField.INDUSTRY_CLASSIFICATION_ENG,
    CompanyField.ACTIVITY,
    CompanyField.COMPANY_SEGMENT,
    CompanyField.COMPANY_SEGMENT_ENG,
    CompanyField.COMPANY_CATEGORY,
    CompanyField.COMPANY_TYPE,
    CompanyField.LISTING_SEGMENT,
    CompanyField.REGISTRAR,
    CompanyField.WEBSITE,
    CompanyField.INSTITUTION_COMMON,
    CompanyField.INSTITUTION_PREFERRED,
    CompanyField.STATUS,
    CompanyField.MARKET_INDICATOR,
    CompanyField.CODE,
    CompanyField.TYPE_BDR,
    CompanyField.REASON,
)

BOOLEAN_FIELDS: tuple[CompanyField, ...] = (
    CompanyField.HAS_BDR,
    CompanyField.HAS_QUOTATION,
    CompanyField.HAS_EMISSIONS,
)


def build_company_facets(
    items: Iterable[CompanyEligibleDTO],
) -> Dict[str, List[str]]:
    """Aggregate available values for each facet field."""

    buckets: Dict[str, set[str]] = {
        field.value: set() for field in (*STRING_FIELDS, *BOOLEAN_FIELDS)
    }

    for item in items:
        for field in STRING_FIELDS:
            value = getattr(item, field.value, None)
            if value:
                buckets[field.value].add(value)

        for field in BOOLEAN_FIELDS:
            value = getattr(item, field.value, None)
            if value is None:
                continue
            buckets[field.value].add("true" if value else "false")

    return {
        key: sorted({v for v in values if v})
        for key, values in buckets.items()
        if values
    }

