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

    # Convenience helpers -------------------------------------------------
    def debug(
        self,
        message: str,
        progress: Optional[dict] = None,
        extra: Optional[dict] = None,
        worker_id: Optional[str] = None,
        show_path: Optional[bool] = None,
    ) -> None:
        """Emit a debug-level log message."""
        self.log(
            message,
            level="debug",
            progress=progress,
            extra=extra,
            worker_id=worker_id,
            show_path=show_path,
        )

    def info(
        self,
        message: str,
        progress: Optional[dict] = None,
        extra: Optional[dict] = None,
        worker_id: Optional[str] = None,
        show_path: Optional[bool] = None,
    ) -> None:
        """Emit an info-level log message."""
        self.log(
            message,
            level="info",
            progress=progress,
            extra=extra,
            worker_id=worker_id,
            show_path=show_path,
        )

    def warning(
        self,
        message: str,
        progress: Optional[dict] = None,
        extra: Optional[dict] = None,
        worker_id: Optional[str] = None,
        show_path: Optional[bool] = None,
    ) -> None:
        """Emit a warning-level log message."""
        self.log(
            message,
            level="warning",
            progress=progress,
            extra=extra,
            worker_id=worker_id,
            show_path=show_path,
        )

    def error(
        self,
        message: str,
        progress: Optional[dict] = None,
        extra: Optional[dict] = None,
        worker_id: Optional[str] = None,
        show_path: Optional[bool] = None,
    ) -> None:
        """Emit an error-level log message."""
        self.log(
            message,
            level="error",
            progress=progress,
            extra=extra,
            worker_id=worker_id,
            show_path=show_path,
        )
