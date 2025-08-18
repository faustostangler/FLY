from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List, TypeVar

R = TypeVar("R")


@dataclass(frozen=True)
class ExecutionResultDTO(Generic[R]):
    """Results and metrics returned by a worker pool run."""

    items: List[R]
    # network_bytes: int = 0
