"""Core execution port definitions for the worker pool interface."""

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    runtime_checkable,
)

from domain.dtos import WorkerTaskDTO

from .logger_port import LoggerPort

R = TypeVar("R")


@runtime_checkable
class WorkerPoolPort(Protocol):
    def run(
        self,
        tasks: Iterable[Tuple[int, Any]],
        processor: Callable[[WorkerTaskDTO], R],
        logger: LoggerPort,
        on_result: Optional[Callable[[R], None]] = None,
        post_callback: Optional[Callable[[List[R]], None]] = None,
    ) -> R: ...
