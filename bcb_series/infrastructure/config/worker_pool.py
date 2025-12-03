from __future__ import annotations

from dataclasses import dataclass, field

# Default maximum number of concurrent worker threads or processes
MAX_WORKERS = 1

# Default queue size for producer/consumer pipelines (commonly 2× workers)
QUEUE_SIZE = 1 # * MAX_WORKERS


@dataclass(frozen=True)
class WorkerPoolConfig:
    """Immutable configuration for local worker pools.

    Attributes:
        max_workers (int): Maximum number of concurrent workers allowed.
        queue_size (int): Maximum number of items that can be queued
            for processing at once.
    """

    # Number of workers available for concurrency
    max_workers: int = field(default=MAX_WORKERS)

    # Maximum queue capacity for pending tasks
    queue_size: int = field(default=QUEUE_SIZE)


def load_worker_pool_config() -> WorkerPoolConfig:
    """Factory function to load worker pool configuration.

    Returns:
        WorkerPoolConfig: Initialized with default values for workers
        and queue size.
    """
    # Construct and return the worker pool configuration
    return WorkerPoolConfig(
        max_workers=MAX_WORKERS,
        queue_size=QUEUE_SIZE,
    )
