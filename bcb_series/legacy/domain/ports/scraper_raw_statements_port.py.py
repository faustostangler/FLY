from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from domain.dto import WorkerTaskDTO
from domain.ports import ConfigPort


@runtime_checkable
class StatementsRawcraperPort(Protocol):
    """Port for fetching raw statement HTML."""

    @property
    def config(self) -> ConfigPort: ...

    def fetch(self, task: WorkerTaskDTO) -> Mapping[str, Any]: ...
