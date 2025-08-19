"""Simple thread pool implementation for executing tasks."""

from __future__ import annotations

import random
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from typing import Any, Callable, Iterable, List, Optional, Tuple, TypeVar

from domain.dtos.worker_task_dto import WorkerTaskDTO

from domain.ports.config_port import ConfigPort
from domain.ports.logger_port import LoggerPort
from domain.ports.metrics_collector_port import MetricsCollectorPort
from domain.ports.worker_pool_port import WorkerPoolPort
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
        self.max_workers = max_workers or self.config.worker_pool.max_workers or 1

    def run(
        self,
        tasks: Iterable[Tuple[int, Any]],
        processor: Callable[[WorkerTaskDTO], R],
        logger: LoggerPort,
        on_result: Optional[Callable[[R], None]] = None,
        post_callback: Optional[Callable[[List[R]], None]] = None,
    ) -> List[R]:
        """Process ``tasks`` concurrently using ``processor``."""
        results: List[R] = []
        queue: Queue = Queue(self.config.worker_pool.queue_size)
        lock = threading.Lock()
        sentinel = object()

        def worker(worker_id: str) -> None:
            while True:
                item = queue.get()
                if item is sentinel:
                    queue.task_done()
                    break
                index, entry = item
                task = WorkerTaskDTO(index=index, data=entry, worker_id=worker_id)
                result = processor(task)
                if isinstance(result, (bytes, str)):
                    self.metrics_collector.add_network_bytes(len(result))
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

        # Final callback after all tasks are done
        if callable(post_callback):
            logger.log("Callable found", level="info")
            post_callback(results)

        return results
