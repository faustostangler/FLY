# infrastructure/repositories/http_cache_repository.py
from __future__ import annotations
from typing import Callable
from sqlalchemy.orm import Session
from infrastructure.models.http_cache_model import HttpCacheModel

class HttpCacheRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def get(self, url: str) -> HttpCacheModel | None:
        with self._session_factory() as s:
            return s.get(HttpCacheModel, url)

    def upsert(self, url: str, etag: str | None, last_modified: str | None, body: bytes | None) -> None:
        with self._session_factory() as s:
            row = s.get(HttpCacheModel, url) or HttpCacheModel(url=url)
            row.etag = etag
            row.last_modified = last_modified
            row.body = body
            s.merge(row)
            s.commit()
