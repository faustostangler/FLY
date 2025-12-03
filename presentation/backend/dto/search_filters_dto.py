"""Pydantic representation of the generic filter tree contract."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from domain.value_objects import SearchFilterTree


class SearchFiltersDTO(BaseModel):
    """Request body wrapper for the reusable search filter tree.

    ``tree`` mirrors the dictionary grammar interpreted by ``FilterBuilder`` and
    documented in :class:`domain.value_objects.search_filter_tree.SearchFilterTree`.
    Keeping the structure explicit in a DTO allows FastAPI to validate the JSON
    received from the frontend (or CLI mocks) before touching the domain layer.
    """

    tree: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Árvore de filtros estruturados compatível com FilterBuilder.",
    )

    def to_domain(self) -> Optional[SearchFilterTree]:
        """Convert the DTO to the domain value object."""

        return SearchFilterTree.from_raw(self.tree)


__all__ = ["SearchFiltersDTO"]

