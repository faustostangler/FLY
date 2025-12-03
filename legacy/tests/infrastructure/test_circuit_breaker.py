from __future__ import annotations

import time

from infrastructure.http.circuit_breaker import BreakerPolicy, CircuitBreakerScraper


class DummyScraper:
    def __init__(self):
        self.calls = 0

    def fetch(self, url: str, headers=None):
        self.calls += 1
        if self.calls <= 3:
            exc = Exception("rate limited")
            setattr(exc, "status_code", 429)
            raise exc
        return b"ok"


class DummyLogger:
    def __init__(self):
        self.events = []

    def log(self, message, level="info", **_):
        self.events.append((level, message))


def test_circuit_breaker_recovers():
    scraper = DummyScraper()
    logger = DummyLogger()
    breaker = CircuitBreakerScraper(
        scraper,
        logger,
        policy=BreakerPolicy(failure_threshold=2, open_seconds=0.1),
    )

    start = time.monotonic()
    for _ in range(2):
        try:
            breaker.fetch("url")
        except Exception:
            pass
    elapsed = time.monotonic() - start
    assert elapsed < 0.1

    start = time.monotonic()
    try:
        breaker.fetch("url")
    except Exception:
        pass
    elapsed = time.monotonic() - start
    assert elapsed >= 0.1

    time.sleep(0.11)
    result = breaker.fetch("url")
    assert result == b"ok"
    assert any(evt[1] == "circuit closed" for evt in logger.events)
