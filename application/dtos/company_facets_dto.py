from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class CompanyFacetsResponseDTO:
    facets: Dict[str, List[str]] = field(default_factory=dict)
