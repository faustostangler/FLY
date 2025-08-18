from __future__ import annotations

from typing import Any, Literal, Mapping, Optional, Protocol, runtime_checkable

LogLevel = Literal["debug", "info", "warning", "error"]

@runtime_checkable
class LoggerPort(Protocol):
    """Contrato estrutural de logger usado pelo domínio."""
    def log(
        self,
        message: str,
        level: LogLevel = "info",
        progress: Optional[Mapping[str, Any]] = None,
        extra: Optional[Mapping[str, Any]] = None,
        worker_id: Optional[str] = None,
        show_path: Optional[bool] = None,
    ) -> None: ...
