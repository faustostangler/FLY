"""Template method base processor for statement workflows."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from domain.ports import LoggerPort


class BaseProcessor(ABC):
    """Base class implementing load-transform-persist template."""

    logger: LoggerPort

    def run(self, *args, **kwargs) -> Any:
        """Execute processing pipeline with logging and timing."""
        start_time = time.monotonic()
        processor_name = self.__class__.__name__
        self.logger.info(f"Starting {processor_name}")
        try:
            data = self.load(*args, **kwargs)
            transformed = self.transform(data)
            result = self.persist(transformed)
        except Exception as exc:  # pragma: no cover - pass through
            self.logger.error(f"{processor_name} failed: {exc!r}")
            raise
        finally:
            elapsed = time.monotonic() - start_time
            self.logger.info(f"Finished {processor_name} in {elapsed:.2f}s")
        return result

    @abstractmethod
    def load(self, *args, **kwargs):
        """Fetch or read raw data."""

    @abstractmethod
    def transform(self, data):
        """Apply domain logic and mapping."""

    @abstractmethod
    def persist(self, data):
        """Persist transformed data or emit events."""
