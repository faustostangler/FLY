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

from application.ports.logger_port import LoggerPort

# Generic type variable for processor return values
R = TypeVar("R")


@runtime_checkable
class WorkerPoolPort(Protocol):
    """Protocol defining the execution interface for a worker pool.

    A worker pool is responsible for distributing tasks to multiple workers,
    coordinating execution, and collecting results. This interface abstracts
    the execution so that different pool implementations (e.g., threads,
    processes, async) can be plugged in consistently.

    Methods:
        run: Execute a collection of tasks through the worker pool.
    """
    def __call__(
        self,
        logger: LoggerPort,

        tasks: Iterable[Tuple[int, Any]],
        processor: Callable[[WorkerTaskDTO], R],
        on_result: Optional[Callable[[R], None]] = None,
        post_callback: Optional[Callable[[List[R]], None]] = None,

        max_workers: Optional[int] = 1,
        *,
        total_size: Optional[int] = None,
    ) -> List[R]:
        ...

    def run(
        self,
        logger: LoggerPort,

        tasks: Iterable[Tuple[int, Any]],
        processor: Callable[[WorkerTaskDTO], R],
        on_result: Optional[Callable[[R], None]] = None,
        post_callback: Optional[Callable[[List[R]], None]] = None,

        max_workers: Optional[int] = 1,
        *,
        total_size: Optional[int] = None,
    ) -> List[R]:
        """Run a batch of tasks using the worker pool.

        Args:
            tasks (Iterable[Tuple[int, Any]]): Tasks represented as (task_id, payload).
            processor (Callable[[WorkerTaskDTO], R]): Function that processes
                a single task and returns a result.
            logger (LoggerPort): Logger used to record progress and errors.
            on_result (Optional[Callable[[R], None]]): Optional callback
                invoked for each result as it is produced.
            post_callback (Optional[Callable[[List[R]], None]]): Optional
                callback invoked once after all tasks complete.

        Returns:
            R: The result type returned by the processor function.
        """
        ...
