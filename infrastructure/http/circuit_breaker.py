"""Circuit breaker decorator to avoid repeated throttling."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class BreakerPolicy:
    """Configuration for the circuit breaker."""

    failure_threshold: int = 3
    open_seconds: float = 20.0


class CircuitBreakerScraper:
    """Wrap a scraper adding open/half-open/closed states."""

    CLOSED, OPEN, HALF = "closed", "open", "half-open"

    def __init__(self, inner, logger, policy: BreakerPolicy = BreakerPolicy()):
        self._inner = inner
        self._logger = logger
        self._p = policy
        self._state = self.CLOSED
        self._fails = 0
        self._until = 0.0
        self._lock = threading.Lock()

    def fetch(self, url: str, headers=None):
        with self._lock:
            now = time.monotonic()
            if self._state == self.OPEN and now < self._until:
                time.sleep(self._until - now)
            if self._state == self.OPEN and now >= self._until:
                self._state = self.HALF
                self._logger.log("circuit half-open", level="warning")

        try:
            resp = self._inner.fetch(url, headers=headers)
            with self._lock:
                self._fails = 0
                if self._state == self.HALF:
                    self._state = self.CLOSED
                    self._logger.log("circuit closed", level="info")
            return resp
        except Exception as e:  # noqa: BLE001
            code = getattr(e, "status_code", None)
            if code in (429, 403):
                with self._lock:
                    self._fails += 1
                    self._logger.log(f"rate limited ({self._fails})", level="warning")
                    if self._fails >= self._p.failure_threshold:
                        self._state = self.OPEN
                        self._until = time.monotonic() + self._p.open_seconds
                        self._logger.log("circuit open", level="error")
            raise
