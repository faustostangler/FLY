"""Structured filter model used by the company search use case."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class CompanyField(str, Enum):
    """Enumeration of filterable company attributes."""

    ISSUING_COMPANY = "issuing_company"
    TRADING_NAME = "trading_name"
    COMPANY_NAME = "company_name"
    CNPJ = "cnpj"
    MARKET = "market"
    INDUSTRY_SECTOR = "industry_sector"
    INDUSTRY_SUBSECTOR = "industry_subsector"
    INDUSTRY_SEGMENT = "industry_segment"
    INDUSTRY_CLASSIFICATION = "industry_classification"
    INDUSTRY_CLASSIFICATION_ENG = "industry_classification_eng"
    ACTIVITY = "activity"
    COMPANY_SEGMENT = "company_segment"
    COMPANY_SEGMENT_ENG = "company_segment_eng"
    COMPANY_CATEGORY = "company_category"
    COMPANY_TYPE = "company_type"
    LISTING_SEGMENT = "listing_segment"
    REGISTRAR = "registrar"
    WEBSITE = "website"
    INSTITUTION_COMMON = "institution_common"
    INSTITUTION_PREFERRED = "institution_preferred"
    STATUS = "status"
    MARKET_INDICATOR = "market_indicator"
    CODE = "code"
    TYPE_BDR = "type_bdr"
    REASON = "reason"
    HAS_BDR = "has_bdr"
    HAS_QUOTATION = "has_quotation"
    HAS_EMISSIONS = "has_emissions"
    DATE_QUOTATION = "date_quotation"
    LAST_DATE = "last_date"
    LISTING_DATE = "listing_date"

    # Backwards compatibility aliases
    SECTOR = INDUSTRY_SECTOR
    SUBSECTOR = INDUSTRY_SUBSECTOR
    SEGMENT = INDUSTRY_SEGMENT
    TICKER = CODE


class ComparisonOperator(str, Enum):
    """Supported comparison operators for company filters."""

    EQUALS = "EQUALS"
    IN = "IN"
    CONTAINS = "CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    BETWEEN = "BETWEEN"


class LogicalOperator(str, Enum):
    """Logical operators that combine filter clauses."""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    def is_negative(self) -> bool:
        """Return ``True`` when the clause is meant to be negated."""

        return self is LogicalOperator.NOT


@dataclass(frozen=True)
class CompanyFilterCondition:
    """A leaf condition applied to a specific field."""

    field: CompanyField
    operator: ComparisonOperator
    values: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CompanyFilterClause:
    """One clause in the structured filter query."""

    logical: LogicalOperator
    condition: CompanyFilterCondition | None = None
    group: "CompanyFilterQuery" | None = None

    def __post_init__(self) -> None:
        has_condition = self.condition is not None
        has_group = self.group is not None
        if has_condition and has_group:
            raise ValueError("A clause cannot have both condition and group")
        if not has_condition and not has_group:
            raise ValueError("A clause must define either a condition or a group")

    def is_group(self) -> bool:
        """Return ``True`` when this clause wraps a nested query."""

        return self.group is not None


@dataclass(frozen=True)
class CompanyFilterQuery:
    """Structured representation of the company search filters."""

    clauses: List[CompanyFilterClause] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Return ``True`` when the query has no active clauses."""

        return len(self.clauses) == 0
