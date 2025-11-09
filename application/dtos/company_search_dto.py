from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .company_search_result_dto import CompanySearchResultDTO

__all__ = ["CompanySearchResponseDTO", "CompanySearchResultDTO"]


@dataclass(frozen=True)
class CompanySearchResponseDTO:
    items: List[CompanySearchResultDTO]
    total: int
    facets: Dict[str, List[str]] = field(default_factory=dict)
