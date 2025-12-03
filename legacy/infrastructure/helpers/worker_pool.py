"""Simple thread pool implementation for executing tasks."""

from __future__ import annotations

import random
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from typing import Any, Callable, Iterable, List, Optional, Tuple, TypeVar

from domain.dto import ExecutionResultDTO, WorkerTaskDTO
from domain.ports import ConfigPort, LoggerPort, MetricsCollectorPort, WorkerPoolPort
from infrastructure.helpers.byte_formatter import ByteFormatter

T = WorkerTaskDTO
R = TypeVar("R")


class WorkerPool(WorkerPoolPort):
    """Simple thread pool implementation tied to the domain
    ``WorkerPoolPort``."""

    def __init__(
        self,
        config: ConfigPort,
        metrics_collector: MetricsCollectorPort,
        max_workers: Optional[int] = None,
    ) -> None:
        """Initialize the worker pool with configuration and metrics."""

        self.config = config
        self.metrics_collector = metrics_collector
        self.max_workers = max_workers or config.global_settings.max_workers or 1
        self.byte_formatter = ByteFormatter()

    def run(
        self,
        tasks: Iterable[Tuple[int, Any]],
        processor: Callable[[T], R],
        logger: LoggerPort,
        on_result: Optional[Callable[[R], None]] = None,
        post_callback: Optional[Callable[[List[R]], None]] = None,
    ) -> ExecutionResultDTO[R]:
        """Process ``tasks`` concurrently using ``processor``."""

        # Inform about the worker pool startup
        # logger.log("Run  Method worker_pool_executor().run()", level="info")

        results: List[R] = []
        queue: Queue = Queue(self.config.global_settings.queue_size)
        lock = threading.Lock()
        sentinel = object()
        start_time = time.perf_counter()

        def worker(worker_id: str) -> None:
            # logger.log("Run  Method worker_pool_executor().worker()", level="info")
            while True:
                item = queue.get()
                if item is sentinel:
                    queue.task_done()
                    # logger.log("End  Method worker_pool_executor().worker()", level="info")
                    break
                index, entry = item
                task = WorkerTaskDTO(index=index, data=entry, worker_id=worker_id)
                # logger.log(f"task: {task}", level="info")
                result = processor(task)
                try:
                    with lock:
                        results.append(result)
                        if callable(on_result):
                            on_result(result)
                except Exception as exc:  # noqa: BLE001
                    logger.log(
                        f"worker error: {exc}", level="warning", worker_id=worker_id
                    )
                finally:
                    queue.task_done()

        with ThreadPoolExecutor(max_workers=self.max_workers) as worker_pool_executor:
            futures = [
                worker_pool_executor.submit(worker, uuid.uuid4().hex[:8])
                for _ in range(self.max_workers)
            ]

            for task in tasks:
                time.sleep(random.uniform(0.0, 0.12))
                queue.put(task)

            for _ in range(self.max_workers):
                queue.put(sentinel)

            queue.join()

            for future in futures:
                future.result()

        elapsed = time.perf_counter() - start_time

        # Package execution metrics (network and processing bytes)
        metrics = self.metrics_collector.get_metrics(elapsed_time=elapsed)

        # Final callback after all tasks are done
        if callable(post_callback):
            logger.log("Callable found", level="info")
            post_callback(results)

        # logger.log("End  Method worker_pool_executor().run()", level="info")
        return ExecutionResultDTO(items=results, metrics=metrics)
