
"""Rate limiter decorator that spaces requests using a shared token bucket.
Exposes the same public API as AffinityHttpClient (fetch, fetch_with, borrow_session).
"""
from __future__ import annotations

import random
import threading
import time
from typing import Any

class TokenBucket:
    def __init__(self, rate_per_sec: float, burst: int):
        self._rate = rate_per_sec
        self._cap = burst
        self._tokens = burst
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def delay(self) -> float:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._last = now
            self._tokens = min(self._cap, self._tokens + elapsed * self._rate)
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return 0.0
            need = (1.0 - self._tokens) / self._rate
        # add jitter to break synchrony
        return need + random.uniform(0.05, 0.25)

class RateLimitedScraper:
    def __init__(self, inner: Any, bucket: TokenBucket, logger: Any):
        self._inner = inner
        self._bucket = bucket
        self._logger = logger

    def _wait(self) -> None:
        d = self._bucket.delay()
        if d:
            time.sleep(d)

    def fetch(self, url: str, headers=None):
        self._wait()
        return self._inner.fetch(url, headers=headers)

    def fetch_with(self, session, url: str, headers=None):
        self._wait()
        return self._inner.fetch_with(session, url, headers=headers)

    def borrow_session(self):
        return self._inner.borrow_session()
