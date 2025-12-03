from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from presentation.backend.dto.search_filters_dto import SearchFiltersDTO


class CompanyAccountsChartRequestDTO(BaseModel):
    company_name: str = Field(..., description="Nome da empresa alvo.")
    accounts: List[str] = Field(..., description="Lista de contas/ratios desejadas.")
    filters: Optional[SearchFiltersDTO] = Field(
        default=None,
        description="Filtro estruturado aplicado ao dataset.",
    )


__all__ = ["CompanyAccountsChartRequestDTO"]

