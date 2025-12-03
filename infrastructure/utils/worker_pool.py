from __future__ import annotations

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from typing import Any, Callable, Iterable, List, Optional, Tuple, TypeVar, cast

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from application.ports.metrics_collector_port import MetricsCollectorPort
from application.ports.worker_pool_port import WorkerPoolPort
from domain.dtos.worker_task_dto import WorkerTaskDTO
from infrastructure.utils.id_generator import IdGenerator

# Generic type variable representing the processor's return type
R = TypeVar("R")


class WorkerPool(WorkerPoolPort):
    """Thread-based worker pool tied to the domain ``WorkerPoolPort``.

    This implementation uses a bounded queue and a fixed-size
    ThreadPoolExecutor to process tasks concurrently. Results are
    accumulated in-memory and optionally streamed via callbacks.

    Notes:
        - Result order is not guaranteed; items are appended as they complete.
        - If the processor returns ``bytes`` or ``str``, their lengths are
          forwarded to ``MetricsCollectorPort`` as network byte counts.
    """

    def __init__(
        self,
        config: ConfigPort,
        metrics_collector: MetricsCollectorPort,
        max_workers: Optional[int] = None,
    ) -> None:
        """Initialize the worker pool.

        Args:
            config (ConfigPort): Configuration provider used to resolve
                queue sizing and default worker count.
            metrics_collector (MetricsCollectorPort): Collector used to
                record simple network byte metrics.
            max_workers (Optional[int]): Explicit worker count. If omitted,
                falls back to ``config.worker_pool.max_workers`` and then to ``1``.
        """
        # Store configuration and metrics collaborators
        self.config = config
        self.metrics_collector = metrics_collector

        # Resolve the effective worker count with safe fallbacks
        self.max_workers = max_workers or self.config.worker_pool.max_workers or 1
        self.generator = IdGenerator(config=self.config)

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
        return self.run(tasks=tasks, processor=processor, logger=logger, on_result=on_result, post_callback=post_callback, max_workers=max_workers, total_size=total_size)

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
        """Process tasks concurrently using the provided processor.

        Each task is a tuple ``(index, data)`` that is wrapped into a
        ``WorkerTaskDTO`` and passed to ``processor``. Results are collected
        and optionally emitted via callbacks.

        Args:
            tasks (Iterable[Tuple[int, Any]]): Iterable of task items as
                ``(index, data)`` pairs to be processed.
            processor (Callable[[WorkerTaskDTO], R]): Function that handles a
                single task DTO and returns a result of type ``R``.
            logger (LoggerPort): Logger used for warnings and informational messages.
            on_result (Optional[Callable[[R], None]]): Optional per-result callback
                invoked immediately after the result is appended.
            post_callback (Optional[Callable[[List[R]], None]]): Optional callback
                invoked once after all tasks are completed, receiving the full list
                of results.

        Returns:
            List[R]: The list of results produced by the processor. The order
            reflects completion timing, not the original task order.

        Notes:
            - Exceptions raised inside the ``processor`` are not caught here and
              will terminate the worker executing that task.
            - The queue is bounded by ``config.worker_pool.queue_size`` to avoid
              unbounded memory growth.
        """
        # Container for processed results
        results: List[R] = []

        # Bounded queue to apply backpressure to producers
        queue: Queue[Any] = Queue(self.config.worker_pool.queue_size)

        # Lock to protect shared writes to the results list and callbacks
        lock = threading.Lock()

        # Sentinel used to signal graceful worker shutdown
        sentinel = object()

        # Worker routine executed by each thread
        def worker(worker_id: str) -> None:
            # Process items until a sentinel is encountered
            while True:
                item = queue.get()
                if item is sentinel:
                    queue.task_done()
                    break

                # Unpack the work item and build a task DTO
                index, entry = cast(Tuple[int, Any], item)
                task = WorkerTaskDTO(index=index, data=entry, worker_id=worker_id, total_size=total_size)

                # Execute the task-specific processor
                result = processor(task)

                # Append result and emit optional per-result callback
                try:
                    with lock:
                        if result is None:
                            continue

                        store_result = True
                        if isinstance(result, list) and len(result) == 0:
                            store_result = False

                        if store_result:
                            results.append(result)
                            if callable(on_result):
                                on_result(result)
                except Exception as exc:  # noqa: BLE001
                    # Log any callback/list append issues without crashing the worker
                    logger.log(
                        f"worker error: {exc}", level="warning", worker_id=worker_id
                    )
                finally:
                    # Mark the queue task as done regardless of outcome
                    queue.task_done()

        # Create a fixed-size pool of worker threads
        with ThreadPoolExecutor(max_workers=max_workers or self.max_workers) as worker_pool_executor:
            # Launch workers with short identifiers for easier logging
            futures = [
                worker_pool_executor.submit(worker, self.generator.create_id(size=8))
                for _ in range(self.max_workers)
            ]

            # Enqueue all incoming tasks with a small jitter to reduce lock contention
            for task in tasks:
                time.sleep(random.uniform(0.0, 0.12))
                queue.put(task)

            # Signal workers to shut down after all tasks are queued
            for _ in range(self.max_workers):
                queue.put(sentinel)

            # Block until the queue is fully drained
            queue.join()

            # Propagate any worker exceptions to the main thread
            for future in futures:
                future.result()

        # Invoke the final callback once all results are ready
        if callable(post_callback):
            logger.log("Callable found", level="info")
            post_callback(results)

        # Return the collected results to the caller
        return results
