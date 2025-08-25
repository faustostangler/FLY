from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.models import BaseModel
from infrastructure.repositories.http_cache_repository import HttpCacheRepository
from infrastructure.scrapers.requests_raw_statement_scraper import (
    RequestsStatementsRawcraper,
)


class DummySession:
    def __init__(self, responses):
        self._responses = responses

    def get(self, url, headers=None, timeout=None, allow_redirects=True):
        return self._responses.pop(0)


class DummyPool:
    def __init__(self, responses):
        self._responses = responses

    def acquire(self, timeout=5.0):
        return DummySession(self._responses)

    def release(self, session):
        pass


class DummyMetrics:
    def __init__(self):
        self.network_bytes = 0

    def record_network_bytes(self, n: int) -> None:
        self.network_bytes += n


class DummyLogger:
    def __init__(self):
        self.msgs = []

    def log(self, msg, level="info", **_):
        self.msgs.append((level, msg))


class FakeResponse(SimpleNamespace):
    def raise_for_status(self):
        pass


def test_cache_serves_304_response():
    engine = create_engine("sqlite:///:memory:", future=True)
    Session = sessionmaker(bind=engine, autoflush=True, expire_on_commit=False)
    BaseModel.metadata.create_all(engine)
    repo = HttpCacheRepository(Session)
    metrics = DummyMetrics()
    logger = DummyLogger()

    first = FakeResponse(
        status_code=200,
        headers={"ETag": "x", "Last-Modified": "y"},
        content=b"data",
    )
    second = FakeResponse(status_code=304, headers={}, content=b"")

    pool = DummyPool([first, second])
    scraper = RequestsStatementsRawcraper(
        pool=pool, cache=repo, logger=logger, metrics=metrics
    )

    body1 = scraper.fetch("http://example.com")
    assert body1 == b"data"
    assert metrics.network_bytes == len(b"data")

    body2 = scraper.fetch("http://example.com")
    assert body2 == b"data"
    assert metrics.network_bytes == len(b"data")
    assert any(msg[1] == "http 304 served from cache" for msg in logger.msgs)
