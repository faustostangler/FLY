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
        self._config = config
        self._logger = logger
        self._q = queue.LifoQueue(maxsize=size)
        self._size = config.http.session_pool_size or size
        self._utils = FetchUtils(self._config, self._logger)

        self._bootstrap()

    def _bootstrap(self) -> None:
        for _ in range(self._size):
            s = self._utils.create_scraper()
            retry = Retry(
                total=self._config.http.retries,
                backoff_factor=self._config.http.backoff_factor,
                status_forcelist=self._config.http.status_forcelist,
                respect_retry_after_header=self._config.http.respect_retry_after_header,
                allowed_methods=frozenset(["GET", "HEAD"]),
            )
            adapter = HTTPAdapter(
                pool_connections=self._config.http.pool_connections, 
                pool_maxsize=self._config.http.pool_maxsize, 
                max_retries=retry
            )
            s.mount("https://", adapter)
            s.mount("http://", adapter)
            self._q.put(s)

    def acquire(self, timeout: float = 5.0) -> requests.Session:
        timeout = self._config.http.timeout_connect or timeout
        return self._q.get(timeout=timeout)

    def release(self, session: requests.Session) -> None:
        self._q.put(session)
