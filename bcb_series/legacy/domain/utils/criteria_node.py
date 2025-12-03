"""Domain value object representing a classification criterion node."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple


@dataclass(frozen=True)
class CriteriaNode:
    """Immutable criteria definition with potential child nodes."""

    target_line: str
    criteria: List[Tuple[str, str, Any]]
    children: List["CriteriaNode"]
