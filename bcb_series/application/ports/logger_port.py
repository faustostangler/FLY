from __future__ import annotations

from typing import Any, Literal, Mapping, Optional, Protocol, runtime_checkable

# NsdTypePolicy log levels for application logging
LogLevel = Literal["debug", "info", "warning", "error"]


@runtime_checkable
class LoggerPort(Protocol):
    """Structural contract for the application's logging system.

    This protocol defines the minimal logging interface expected
    by the domain layer. Implementations can route logs to different
    backends such as console, files, or external monitoring systems.

    Methods:
        log(message, level, progress, extra, worker_id, show_path):
            Emit a log entry with optional metadata.
    """

    def log(
        self,
        message: str,
        level: LogLevel = "info",
        progress: Optional[Mapping[str, Any]] = None,
        extra: Optional[Mapping[str, Any]] = None,
        worker_id: Optional[str] = None,
        show_path: Optional[bool] = None,
    ) -> None:
        """Log a message with optional metadata.

        Args:
            message (str): The log message text.
            level (LogLevel, optional): Severity level of the log entry.
                Defaults to "info".
            progress (Mapping[str, Any], optional): Progress information,
                such as counters or percentages.
            extra (Mapping[str, Any], optional): Arbitrary additional metadata
                for the log record.
            worker_id (str, optional): Identifier of the worker emitting the log.
            show_path (bool, optional): Whether to display file path information
                along with the message.

        Returns:
            None
        """
        ...
