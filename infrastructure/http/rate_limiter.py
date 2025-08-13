"""Process-wide token bucket limiter with jitter."""

from __future__ import annotations

import random
import threading
import time


class TokenBucket:
    """Simple token bucket allowing ``rate_per_sec`` requests."""

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
        return need + random.uniform(0.05, 0.25)  # jitter breaks synchrony


class RateLimitedScraper:
    """Decorator that applies ``TokenBucket`` delays to a scraper."""

    def __init__(self, inner, bucket: TokenBucket, logger):
        self._inner = inner
        self._bucket = bucket
        self._logger = logger

    def fetch(self, url: str, headers=None):
        d = self._bucket.delay()
        if d:
            time.sleep(d)
        return self._inner.fetch(url, headers=headers)
