from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .company_search_result_dto import CompanySearchResultDTO

__all__ = ["CompanySearchResponseDTO", "CompanySearchResultDTO"]


@dataclass(frozen=True)
class CompanySearchResponseDTO:
    items: List[CompanySearchResultDTO]
    total: int
