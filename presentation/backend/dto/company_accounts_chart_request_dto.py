from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from presentation.backend.dto.search_filters_dto import SearchFiltersDTO


class CompanyAccountsChartRequestDTO(BaseModel):
    company_name: str = Field(..., description="Company name to fetch ratios for")
    accounts: List[str] = Field(..., description="List of account codes to plot")
    filters: Optional[SearchFiltersDTO] = Field(default=None, description="Structured filters")
