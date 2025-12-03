from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List, TypeVar

T = TypeVar("T")

@dataclass(frozen=True, kw_only=True)
class SyncResultsDTO(Generic[T]):
    items: List[T]
    metrics: int
