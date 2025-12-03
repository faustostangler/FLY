from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from application.ports.logger_port import LoggerPort


@dataclass(frozen=True)
class LoggerFacade:
    """Lightweight facade around a LoggerPort implementation.

    Provides a simplified logging interface that enforces consistent
    log levels (`debug`, `info`, `warning`, `error`) while delegating
    the actual work to the injected `LoggerPort` instance.

    Attributes:
        _inner (LoggerPort): Concrete logger implementation used internally.
    """

    _inner: LoggerPort

    def log(self, *a, **kw) -> None:
        """Forward a raw log call directly to the underlying logger."""
        self._inner.log(*a, **kw)

    def debug(
        self,
        message: str,
        *,
        progress: Optional[Mapping[str, Any]] = None,
        extra: Optional[Mapping[str, Any]] = None,
        worker_id: Optional[str] = None,
        show_path: Optional[bool] = None,
    ) -> None:
        """Log a message at DEBUG level with optional structured metadata.

        Args:
            message (str): Log message content.
            progress (Optional[Mapping[str, Any]]): Progress information (e.g., counters).
            extra (Optional[Mapping[str, Any]]): Arbitrary extra structured data.
            worker_id (Optional[str]): Identifier of the worker emitting the log.
            show_path (Optional[bool]): Whether to include source path in the log.
        """
        self._inner.log(
            message,
            level="debug",
            progress=progress,
            extra=extra,
            worker_id=worker_id,
            show_path=show_path,
        )

    def info(self, message: str, **kw) -> None:
        """Log a message at INFO level."""
        self._inner.log(message, level="info", **kw)

    def warning(self, message: str, **kw) -> None:
        """Log a message at WARNING level."""
        self._inner.log(message, level="warning", **kw)

    def error(self, message: str, **kw) -> None:
        """Log a message at ERROR level."""
        self._inner.log(message, level="error", **kw)
