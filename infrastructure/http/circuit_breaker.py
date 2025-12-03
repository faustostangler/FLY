# infrastructure/http/circuit_breaker.py
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BreakerPolicy:
    failure_threshold: int = 3
    open_seconds: float = 20.0

class CircuitBreakerClient:
    CLOSED, OPEN, HALF = "closed", "open", "half"
    def __init__(self, inner: Any, logger: Any | None, policy: BreakerPolicy = BreakerPolicy()) -> None:
        self._inner, self._logger, self._p = inner, logger, policy
        self._state, self._fails, self._until = self.CLOSED, 0, 0.0
        self._lock = threading.Lock()

    def _pre(self) -> None:
        with self._lock:
            now = time.monotonic()
            if self._state == self.OPEN and now < self._until:
                sleep_for = self._until - now
            else:
                sleep_for = 0.0
        if sleep_for > 0:
            time.sleep(sleep_for)
        with self._lock:
            if self._state == self.OPEN and time.monotonic() >= self._until:
                self._state = self.HALF
                if self._logger:
                    self._logger.log("circuit half-open", level="warning")

    def _post_success(self) -> None:
        with self._lock:
            self._fails = 0
            if self._state == self.HALF:
                self._state = self.CLOSED
                if self._logger:
                    self._logger.log("circuit closed", level="info")

    def _post_failure(self, e: Exception) -> None:
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

    def fetch(self, url: str, headers=None):
        self._pre()
        try:
            r = self._inner.fetch(url, headers=headers); self._post_success(); return r
        except Exception as e:  # noqa: BLE001
            self._post_failure(e); raise

    def fetch_with(self, session, url: str, headers=None):
        self._pre()
        try:
            r = self._inner.fetch_with(session, url, headers=headers); self._post_success(); return r
        except Exception as e:  # noqa: BLE001
            self._post_failure(e); raise

    def borrow_session(self):
        return self._inner.borrow_session()
