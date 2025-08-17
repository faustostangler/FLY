from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from domain.ports import LoggerPort


@dataclass(frozen=True)
class LoggerFacade:
    _inner: LoggerPort

    def log(self, *a, **kw) -> None:
        self._inner.log(*a, **kw)

    def debug(self, message: str, *,
              progress: Optional[Mapping[str, Any]] = None,
              extra: Optional[Mapping[str, Any]] = None,
              worker_id: Optional[str] = None,
              show_path: Optional[bool] = None) -> None:
        self._inner.log(message, level="debug", progress=progress, extra=extra,
                        worker_id=worker_id, show_path=show_path)

    def info(self, message: str, **kw) -> None:
        self._inner.log(message, level="info", **kw)

    def warning(self, message: str, **kw) -> None:
        self._inner.log(message, level="warning", **kw)

    def error(self, message: str, **kw) -> None:
        self._inner.log(message, level="error", **kw)
