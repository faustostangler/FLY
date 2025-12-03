"""Domain entity representing an eligible company for ratios processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple, TYPE_CHECKING


if TYPE_CHECKING:  # pragma: no cover - used for type checkers only
    from domain.dtos.company_data_dto import CodeDTO


@dataclass(frozen=True)
class EligibleCompany:
    """Immutable representation of a company deemed eligible for processing."""

    id: int | None = None
    cvm_code: str | None = None
    issuing_company: str | None = None
    trading_name: str | None = None
    company_name: str | None = None
    cnpj: str | None = None

    ticker_codes: Tuple[str, ...] = field(default_factory=tuple)
    isin_codes: Tuple[str, ...] = field(default_factory=tuple)
    other_codes: Tuple["CodeDTO", ...] = field(default_factory=tuple)
    market: str | None = None

    industry_sector: str | None = None
    industry_subsector: str | None = None
    industry_segment: str | None = None
    industry_classification: str | None = None
    industry_classification_eng: str | None = None
    activity: str | None = None

    company_segment: str | None = None
    company_segment_eng: str | None = None
    company_category: str | None = None
    company_type: str | None = None

    listing_segment: str | None = None
    registrar: str | None = None
    website: str | None = None
    institution_common: str | None = None
    institution_preferred: str | None = None

    status: str | None = None
    market_indicator: str | None = None
    code: str | None = None
    has_bdr: bool | None = None
    type_bdr: str | None = None
    has_quotation: bool | None = None
    has_emissions: bool | None = None

    date_quotation: datetime | None = None
    last_date: datetime | None = None
    listing_date: datetime | None = None

    reason: str | None = None
