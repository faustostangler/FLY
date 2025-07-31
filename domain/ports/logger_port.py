from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class LoggerPort(ABC):
    """Minimal logger interface used across the domain."""

    @abstractmethod
    def log(
        self,
        message: str,
        level: str = "info",
        progress: Optional[dict] = None,
        extra: Optional[dict] = None,
        worker_id: Optional[str] = None,
        show_path: Optional[bool] = None,
    ) -> None:
        """Emit a log message from a worker or service."""
        raise NotImplementedError

    def warning(
        self,
        message: str,
        *args,
        progress: Optional[dict] = None,
        extra: Optional[dict] = None,
        worker_id: Optional[str] = None,
        show_path: Optional[bool] = None,
    ) -> None:
        """Convenience wrapper to log a warning-level message."""
        formatted = message % args if args else message
        self.log(
            formatted,
            level="warning",
            progress=progress,
            extra=extra,
            worker_id=worker_id,
            show_path=show_path,
        )
