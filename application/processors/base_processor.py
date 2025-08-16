"""Template method base processor for statement workflows."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from domain.ports import LoggerPort

L = TypeVar("L")  # Tipo retornado por load()
T = TypeVar("T")  # Tipo retornado por transform()
P = TypeVar("P")  # Tipo retornado por persist() e run()


class BaseProcessor(ABC, Generic[L, T, P]):
    """Base class implementing load-transform-persist template."""

    logger: LoggerPort

    @abstractmethod
    def run(self, *args, **kwargs) -> P:
        """Execute processing pipeline with logging and timing."""

    @abstractmethod
    def load(self, *args, **kwargs) -> L:
        """Fetch or read raw data."""

    @abstractmethod
    def transform(self, data: L) -> T:
        """Apply domain logic and mapping."""

    @abstractmethod
    def persist(self, data: T) -> P:
        """Persist transformed data or emit events."""
