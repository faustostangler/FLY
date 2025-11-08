"""Structured filter model used by the company search use case."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class CompanyField(str, Enum):
    """Enumeration of filterable company attributes."""

    COMPANY_NAME = "company_name"
    TRADING_NAME = "trading_name"
    ISSUING_COMPANY = "issuing_company"
    CNPJ = "cnpj"
    CVM_CODE = "cvm_code"

    MARKET = "market"
    INDUSTRY_SECTOR = "industry_sector"
    SECTOR = "industry_sector"  # legacy alias
    INDUSTRY_SUBSECTOR = "industry_subsector"
    SUBSECTOR = "industry_subsector"  # legacy alias
    INDUSTRY_SEGMENT = "industry_segment"
    SEGMENT = "industry_segment"  # legacy alias
    INDUSTRY_CLASSIFICATION = "industry_classification"
    INDUSTRY_CLASSIFICATION_ENG = "industry_classification_eng"

    COMPANY_CATEGORY = "company_category"
    COMPANY_TYPE = "company_type"
    LISTING_SEGMENT = "listing_segment"
    REGISTRAR = "registrar"

    INSTITUTION_COMMON = "institution_common"
    INSTITUTION_PREFERRED = "institution_preferred"

    STATUS = "status"
    MARKET_INDICATOR = "market_indicator"
    CODE = "code"
    TICKER = "code"  # legacy alias

    HAS_BDR = "has_bdr"
    TYPE_BDR = "type_bdr"
    HAS_QUOTATION = "has_quotation"
    HAS_EMISSIONS = "has_emissions"


class ComparisonOperator(str, Enum):
    """Supported comparison operators for company filters."""

    EQUALS = "EQUALS"
    IN = "IN"
    CONTAINS = "CONTAINS"
    STARTS_WITH = "STARTS_WITH"


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
