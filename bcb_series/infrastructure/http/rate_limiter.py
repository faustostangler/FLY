# infrastructure/http/rate_limiter.py
from __future__ import annotations

import random
import threading
import time
from typing import Any


class TokenBucket:
    def __init__(self, rate_per_sec: float, burst: int) -> None:
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
        return need + random.uniform(0.05, 0.25)

class RateLimitedClient:
    def __init__(self, inner: Any, bucket: TokenBucket, logger: Any | None) -> None:
        self._inner, self._bucket, self._logger = inner, bucket, logger

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
