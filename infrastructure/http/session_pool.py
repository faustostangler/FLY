"""Thread-safe pool of reusable ``requests.Session`` objects."""

from __future__ import annotations

import queue

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from domain.ports import ConfigPort, LoggerPort
from infrastructure.helpers.fetch_utils import FetchUtils


class SessionPool:
    """Manage a bounded set of reusable HTTP sessions."""

    def __init__(self, config: ConfigPort, logger: LoggerPort, size: int = 4):
        self._q = queue.LifoQueue(maxsize=size)
        self._config = config
        self._logger = logger
        self._size = size
        self._bootstrap()

    def _bootstrap(self) -> None:
        for _ in range(self._size):
            s = FetchUtils(self._config, self._logger).create_scraper()
            retry = Retry(
                total=5,
                backoff_factor=0.4,
                status_forcelist=[429, 500, 502, 503, 504],
                respect_retry_after_header=True,
                allowed_methods=frozenset(["GET", "HEAD"]),
            )
            adapter = HTTPAdapter(
                pool_connections=8, pool_maxsize=32, max_retries=retry
            )
            s.mount("https://", adapter)
            s.mount("http://", adapter)
            # Fewer TCP teardowns; plays nicer with anti-bot heuristics
            s.headers.update({"Connection": "keep-alive"})
            self._q.put(s)

    def acquire(self, timeout: float = 5.0) -> requests.Session:
        return self._q.get(timeout=timeout)

    def release(self, session: requests.Session) -> None:
        self._q.put(session)
