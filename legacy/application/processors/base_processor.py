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
        start_time = time.monotonic()
        processor_name = self.__class__.__name__
        self.logger.info(f"Starting {processor_name}")
        try:
            data: L = self.load(*args, **kwargs)
            transformed: T = self.transform(data)
            result: P = self.persist(transformed)
        except Exception as exc:  # pragma: no cover - pass through
            self.logger.error(f"{processor_name} failed: {exc!r}")
            raise
        finally:
            elapsed = time.monotonic() - start_time
            self.logger.info(f"Finished {processor_name} in {elapsed:.2f}s")
        return result

    @abstractmethod
    def load(self, *args, **kwargs) -> L:
        """Fetch or read raw data."""

    @abstractmethod
    def transform(self, data: L) -> T:
        """Apply domain logic and mapping."""

    @abstractmethod
    def persist(self, data: T) -> P:
        """Persist transformed data or emit events."""
