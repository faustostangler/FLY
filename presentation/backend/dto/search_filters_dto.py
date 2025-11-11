from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from domain.value_objects import SearchFilterTree


class SearchFiltersDTO(BaseModel):
    """Pydantic representation of the structured search filter tree."""

    tree: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured filter tree compatible with FilterBuilder.",
    )

    def to_domain(self) -> Optional[SearchFilterTree]:
        """Convert the DTO into the domain value object."""

        return SearchFilterTree.from_raw(self.tree)
