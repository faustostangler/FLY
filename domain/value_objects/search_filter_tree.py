from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


FilterDict = Dict[str, Any]


@dataclass(frozen=True)
class SearchFilterTree:
    """Immutable value object describing a structured filter tree.

    The internal representation matches the structure consumed by
    :class:`FilterBuilder`, where logical operators (``and``/``or``/``not``)
    compose leaves that express field-level conditions.
    """

    raw: FilterDict

    @classmethod
    def from_raw(cls, data: Optional[Any]) -> Optional["SearchFilterTree"]:
        """Create a :class:`SearchFilterTree` from ``dict`` or ``None``.

        Args:
            data: ``dict`` describing the tree, another ``SearchFilterTree``
                instance, or ``None``.
        """
        if data is None:
            return None
        if isinstance(data, SearchFilterTree):
            return data
        if not isinstance(data, dict):
            raise TypeError(
                "SearchFilterTree.from_raw expects a dict or SearchFilterTree instance, "
                f"received {type(data)!r}"
            )
        return cls(raw=data)

    def to_dict(self) -> FilterDict:
        """Expose the tree as a raw ``dict`` for lower layers."""

        return self.raw

    def is_empty(self) -> bool:
        """Return ``True`` when the tree has no conditions."""

        return not bool(self.raw)

    def to_hash(self) -> str:
        """Return a deterministic hash for cache keys and comparisons."""

        if self.is_empty():
            return hashlib.sha256(b"EMPTY_FILTER").hexdigest()

        payload = json.dumps(self.raw, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
