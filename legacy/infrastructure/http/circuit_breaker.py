
"""Circuit breaker decorator to avoid repeated throttling.
Compatible with AffinityHttpClient: passes through fetch, fetch_with and borrow_session.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class BreakerPolicy:
    """Configuration for the circuit breaker."""
    failure_threshold: int = 3
    open_seconds: float = 20.0

class CircuitBreakerScraper:
    """Wrap a scraper adding open/half-open/closed states and exposing the same public API."""

    CLOSED, OPEN, HALF = "closed", "open", "half-open"

    def __init__(self, inner: Any, logger: Any, policy: BreakerPolicy = BreakerPolicy()):
        self._inner = inner
        self._logger = logger
        self._p = policy
        self._state = self.CLOSED
        self._fails = 0
        self._until = 0.0
        self._lock = threading.Lock()

    # ----------------- public API (mirrors AffinityHttpClient) -----------------

    def fetch(self, url: str, headers=None):
        self._pre()
        try:
            resp = self._inner.fetch(url, headers=headers)
            self._post_success()
            return resp
        except Exception as e:  # noqa: BLE001
            self._post_failure(e)
            raise

    def fetch_with(self, session, url: str, headers=None):
        self._pre()
        try:
            resp = self._inner.fetch_with(session, url, headers=headers)
            self._post_success()
            return resp
        except Exception as e:  # noqa: BLE001
            self._post_failure(e)
            raise

    def borrow_session(self):
        return self._inner.borrow_session()

    # ----------------- internal helpers -----------------

    def _pre(self) -> None:
        """Before each call: if OPEN, either sleep until close time or switch to HALF."""
        with self._lock:
            now = time.monotonic()
            if self._state == self.OPEN and now < self._until:
                # Sleep outside of the lock to not block other threads trying to check
                sleep_for = self._until - now
            else:
                sleep_for = 0.0

        if sleep_for > 0:
            time.sleep(sleep_for)

        with self._lock:
            now = time.monotonic()
            if self._state == self.OPEN and now >= self._until:
                self._state = self.HALF
                if self._logger:
                    self._logger.log("circuit half-open", level="warning")

    def _post_success(self) -> None:
        """Reset counters; if HALF, close the circuit on a successful probe."""
        with self._lock:
            self._fails = 0
            if self._state == self.HALF:
                self._state = self.CLOSED
                if self._logger:
                    self._logger.log("circuit closed", level="info")

    def _post_failure(self, e: Exception) -> None:
        """On 429/403 increment failure counter; if threshold reached, open the circuit."""
        code = getattr(e, "status_code", None)
        if code not in (429, 403):
            return
        with self._lock:
            self._fails += 1
            if self._logger:
                self._logger.log(f"rate limited ({self._fails})", level="warning")
            if self._fails >= self._p.failure_threshold:
                self._state = self.OPEN
                self._until = time.monotonic() + self._p.open_seconds
                if self._logger:
                    self._logger.log("circuit open", level="error")
