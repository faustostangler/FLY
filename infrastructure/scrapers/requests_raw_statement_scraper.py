"""HTTP scraper with connection pooling and conditional GET."""

from __future__ import annotations

from requests import Response

from infrastructure.http.session_pool import SessionPool
from infrastructure.repositories.http_cache_repository import HttpCacheRepository


class RequestsRawStatementScraper:
    """Fetch bytes for a URL, reusing connections and honoring ETag/Last-
    Modified."""

    def __init__(
        self,
        pool: SessionPool,
        cache: HttpCacheRepository,
        timeout: tuple[float, float] = (5.0, 20.0),
        logger=None,
        metrics=None,
    ) -> None:
        self._pool = pool
        self._cache = cache
        self._timeout = timeout
        self._logger = logger
        self._metrics = metrics

    def fetch(self, url: str, headers=None) -> bytes:
        cached = self._cache.get(url)
        hdrs = dict(headers or {})
        if cached and cached.etag:
            hdrs["If-None-Match"] = cached.etag
        if cached and cached.last_modified:
            hdrs["If-Modified-Since"] = cached.last_modified

        s = self._pool.acquire()
        try:
            r: Response = s.get(
                url, headers=hdrs, timeout=self._timeout, allow_redirects=True
            )
        finally:
            self._pool.release(s)

        if r.status_code == 304 and cached and cached.body is not None:
            if self._logger:
                self._logger.log("http 304 served from cache", level="info")
            return cached.body

        if r.status_code in (429, 403):
            ex = Exception("rate limited")
            setattr(ex, "status_code", r.status_code)
            raise ex

        r.raise_for_status()

        body = r.content or b""
        self._cache.upsert(
            url,
            etag=r.headers.get("ETag"),
            last_modified=r.headers.get("Last-Modified"),
            body=body,
        )
        if self._metrics:
            self._metrics.record_network_bytes(len(body))
        return body


# Backward compatibility for legacy imports
RawStatementScraper = RequestsRawStatementScraper
