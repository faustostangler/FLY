from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from domain.dtos import WorkerTaskDTO

# from domain.ports import ConfigPort


@runtime_checkable
class RawStatementScraperPort(Protocol):
    """Port for fetching raw statement HTML."""

    def fetch(self, task: WorkerTaskDTO) -> Mapping[str, Any]: ...

    # @property
    # def config(self) -> ConfigPort: ...
