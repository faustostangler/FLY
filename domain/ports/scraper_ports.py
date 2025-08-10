from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from domain.ports import ConfigPort
from domain.dto import WorkerTaskDTO


@runtime_checkable
class RawStatementScraperPort(Protocol):
    """Port for fetching raw statement HTML."""

    @property
    def config(self) -> ConfigPort: ...

    def fetch(self, task: WorkerTaskDTO) -> Mapping[str, Any]: ...
