from __future__ import annotations

from dataclasses import dataclass, field

MAX_WORKERS = 1 # 20 Default number of threads for sync operations
QUEUE_SIZE = 2 * MAX_WORKERS  # Max queue size for producer/consumer pipeline


@dataclass(frozen=True)
class WorkerPoolConfig:
    """General settings for web scraping.

    Attributes:
        test_internet: URL used to check connectivity.
        timeout: Maximum wait time for each request.
        max_attempts: Maximum retry attempts if a request fails.
        user_agents: List of user-agent strings loaded from ``user_agents.json``.
        referers: List of referer strings loaded from ``referers.json``.
        languages: List of Accept-Language headers from ``languages.json``.
    """

    max_workers: int = field(default=MAX_WORKERS)
    queue_size: int = field(default=QUEUE_SIZE)


def load_worker_pool_config() -> WorkerPoolConfig:
    """Create a :class:`ScrapingConfig` from bundled JSON files."""
    return WorkerPoolConfig(
        max_workers=MAX_WORKERS,
        queue_size=QUEUE_SIZE,
    )
