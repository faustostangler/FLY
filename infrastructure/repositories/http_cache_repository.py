"""Repository for persisted HTTP cache rows."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from infrastructure.models.http_cache_model import HttpCacheModel


class HttpCacheRepository:
    """Repository for persisted HTTP cache rows.

    Expects a callable that returns a SQLAlchemy Session when invoked.
    """

    def __init__(self, session_factory: Callable[[], Session]):
        """Initialize repository with a session factory."""
        self._session_factory = session_factory

    def get(self, url: str) -> HttpCacheModel | None:
        """Return cached row for ``url`` if present."""
        with self._session_factory() as s:
            return s.get(HttpCacheModel, url)

    def upsert(
        self, url: str, etag: str | None, last_modified: str | None, body: bytes
    ) -> None:
        """Insert or update cache metadata and body for ``url``."""
        with self._session_factory() as s:
            row = s.get(HttpCacheModel, url) or HttpCacheModel(url=url)
            row.etag = etag
            row.last_modified = last_modified
            row.body = body
            s.add(row)
            s.commit()
