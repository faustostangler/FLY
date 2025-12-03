from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class CompanyFacetsResponseDTO(BaseModel):
    facets: Dict[str, List[str]] = Field(default_factory=dict)
