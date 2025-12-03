"""Domain value object encapsulating the generic filter tree structure.

The project already relied on dictionaries that follow the grammar consumed by
``FilterBuilder``.  This value object adds a thin but explicit contract so the
same structure can be shared across CLI, FastAPI and the frontend without
passing loose dictionaries around.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


FilterDict = Dict[str, Any]


@dataclass(frozen=True)
class SearchFilterTree:
    """Immutable representation of the search filter grammar.

    ``raw`` must respect the specification expected by ``FilterBuilder``.  The
    structure is a recursive tree where internal nodes are logical operators and
    leaves describe column conditions.  Examples::

        {"and": [{"status": "ATIVO"}, {"market": {"in": ["NM", "N2"]}}]}
        {"or": [
            {"has_bdr": True},
            {"listing_date": {">=": "2020-01-01"}},
        ]}

    Leaves accept comparison operators (``==``, ``!=``, ``in``, ``between``),
    text matching (``contains``, ``startswith`` ...) and null checks, mirroring
    what ``FilterBuilder`` already supports.
    """

    raw: FilterDict

    @classmethod
    def from_raw(cls, data: Optional[Any]) -> Optional["SearchFilterTree"]:
        """Create a :class:`SearchFilterTree` from ``dict``/VO/``None``.

        ``None`` is propagated so callers can easily short-circuit when no
        filter is provided.  Passing something different from the supported
        types raises :class:`TypeError` so bugs surface early.
        """

        if data is None:
            return None
        if isinstance(data, SearchFilterTree):
            return data
        if not isinstance(data, dict):
            raise TypeError(
                "SearchFilterTree.from_raw expects a dict-compatible tree; "
                f"received {type(data)!r}."
            )
        return cls(raw=data)

    def to_dict(self) -> FilterDict:
        """Return the underlying dictionary compatible with ``FilterBuilder``."""

        return self.raw

    def is_empty(self) -> bool:
        """``True`` when the tree has no conditions configured."""

        return not bool(self.raw)

    def to_hash(self) -> str:
        """Return a deterministic SHA-256 hash for the tree structure."""

        if self.is_empty():
            return self._empty_hash()

        payload = json.dumps(self.raw, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def filtered_by_fields(
        self,
        allowed: set[str],
    ) -> Optional["SearchFilterTree"]:
        """Return a copy of the tree keeping only leaves for ``allowed`` fields.

        Logical nodes (``and``/``or``/``not``) are collapsed when all children are
        pruned. Returns ``None`` when no condition survives.
        """

        if self.is_empty():
            return None

        def _filter_node(node: Any) -> Any | None:
            if isinstance(node, dict):
                keys = set(node.keys())

                if keys == {"and"}:
                    children = [_filter_node(child) for child in node["and"]]
                    children = [child for child in children if child is not None]
                    if not children:
                        return None
                    return {"and": children}

                if keys == {"or"}:
                    children = [_filter_node(child) for child in node["or"]]
                    children = [child for child in children if child is not None]
                    if not children:
                        return None
                    return {"or": children}

                if keys == {"not"}:
                    child = _filter_node(node["not"])
                    if child is None:
                        return None
                    return {"not": child}

                if len(node) == 1:
                    field, condition = next(iter(node.items()))
                    if field in allowed:
                        return {field: condition}
                    return None

                return node

            if isinstance(node, list):
                children = [_filter_node(child) for child in node]
                children = [child for child in children if child is not None]
                if not children:
                    return None
                return children

            return None

        filtered = _filter_node(self.raw)
        if filtered is None:
            return None
        return SearchFilterTree(raw=filtered)

    @staticmethod
    def _empty_hash() -> str:
        return hashlib.sha256(b"EMPTY_FILTER").hexdigest()


__all__ = ["SearchFilterTree"]

