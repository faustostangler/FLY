from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List, TypeVar

# Generic type for result items
R = TypeVar("R")


@dataclass(frozen=True)
class ExecutionResultDTO(Generic[R]):
    """Data transfer object representing the outcome of a worker pool execution.

    Attributes:
        items (List[R]): Collection of processed items returned by workers.
    """

    # List of results produced by the worker pool
    items: List[R]
