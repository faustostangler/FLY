from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class CompanyFilterConditionDTO(BaseModel):
    field: str
    operator: str = Field(default="IN")
    values: List[str] = Field(default_factory=list)


class CompanyFilterClauseDTO(BaseModel):
    logical: str = Field(default="AND")
    condition: Optional[CompanyFilterConditionDTO] = None
    group: Optional["CompanyFilterQueryDTO"] = None

    @model_validator(mode="after")
    def check_structure(self):
        condition, group = self.condition, self.group
        if condition is None and group is None:
            raise ValueError(
                "Each clause must provide either a condition or a nested group"
            )
        if condition is not None and group is not None:
            raise ValueError(
                "A clause cannot define both a condition and a nested group"
            )
        return self


class CompanyFilterQueryDTO(BaseModel):
    clauses: List[CompanyFilterClauseDTO] = Field(default_factory=list)


CompanyFilterClauseDTO.update_forward_refs()


class CompanySearchResultDTO(BaseModel):
    company_name: str
    trading_name: Optional[str] = None
    tickers: List[str] = Field(default_factory=list)
    market: Optional[str] = None
    industry_sector: Optional[str] = None
    industry_subsector: Optional[str] = None
    industry_segment: Optional[str] = None
    institution_common: Optional[str] = None
    institution_preferred: Optional[str] = None


class CompanySearchResponseDTO(BaseModel):
    items: List[CompanySearchResultDTO]
    total: int
    facets: Dict[str, List[str]] = Field(default_factory=dict)
