from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from domain.dtos import WorkerTaskDTO

# from domain.ports import ConfigPort


@runtime_checkable
class ScraperStatementRawPort(Protocol):
    """Protocol defining the scraping interface for raw financial statements.

    This port abstracts the mechanism used to fetch HTML statements so that
    implementations can vary (e.g., HTTP requests, cached sources, headless
    browsers) without impacting the domain logic.

    Methods:
        fetch(task: WorkerTaskDTO) -> Mapping[str, Any]:
            Retrieve the raw HTML of a financial statement for the given task.
            The return value should be a mapping containing raw content
            and any relevant metadata.
    """

    def fetch(self, task: WorkerTaskDTO) -> Mapping[str, Any]: ...
    # Future extension: expose config if needed for scraper customization
    # @property
    # def config(self) -> ConfigPort: ...
