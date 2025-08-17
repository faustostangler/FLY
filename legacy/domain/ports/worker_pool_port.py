"""Core execution port definitions for the worker pool interface."""

from __future__ import annotations

from typing import Any, Callable, Iterable, List, Optional, Protocol, Tuple, TypeVar

from domain.dto import ExecutionResultDTO, WorkerTaskDTO

from .logger_port import LoggerPort

T = WorkerTaskDTO
R = TypeVar("R")


class WorkerPoolPort(Protocol):
    def run(
        self,
        tasks: Iterable[Tuple[int, Any]],
        processor: Callable[[T], R],
        logger: LoggerPort,
        on_result: Optional[Callable[[R], None]] = None,
        post_callback: Optional[Callable[[List[R]], None]] = None,
    ) -> ExecutionResultDTO[R]:
        """Execute tasks concurrently using worker threads."""

        raise NotImplementedError
