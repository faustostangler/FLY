# infrastructure/http/cloudscraper_affinity_http_client.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator

import requests

try:
    import cloudscraper  # type: ignore
except Exception:  # noqa: BLE001
    cloudscraper = None  # fallback control

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from application.ports.http_client_port import AffinityHttpClientPort
from application.ports.logger_port import LoggerPort
from infrastructure.adapters.engine_setup import EngineSetup
from infrastructure.config.scraping import load_scraping_config
from infrastructure.http.backoff import sleep_expo_jitter
from infrastructure.http.headers_pool import HeadersPool
from infrastructure.repositories.http_cache_repository import HttpCacheRepository


class CloudscraperAffinityHttpClient(AffinityHttpClientPort, EngineSetup):
    """Cliente HTTP com Cloudscraper, randomização de headers, pool, retries, backoff e cache condicional."""

    def __init__(self, connection_string: str, logger: LoggerPort) -> None:
        EngineSetup.__init__(self, connection_string, logger)
        self._cfg = load_scraping_config()
        self._pool = HeadersPool.from_config()
        self._cache = HttpCacheRepository(self.Session)

    # ---------- sessão com pool + retries ----------
    def _make_adapter(self) -> HTTPAdapter:
        retry = Retry(
            total=self._cfg.max_attempts,
            connect=self._cfg.max_attempts,
            read=self._cfg.max_attempts,
            status=self._cfg.max_attempts,
            backoff_factor=0.5,
            allowed_methods=frozenset(["GET", "HEAD"]),
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        return HTTPAdapter(max_retries=retry, pool_connections=32, pool_maxsize=32)

    def _create_session(self) -> requests.Session:
        if cloudscraper is not None:
            s = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
        else:
            s = requests.Session()
        adapter = self._make_adapter()
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        # sorteio inicial por sessão
        s.headers.update(self._pool.sample())
        return s

    # ---------- condicional ETag/Last-Modified ----------
    def _apply_conditional_headers(self, url: str, headers: Dict[str, str]) -> Dict[str, str]:
        row = self._cache.get(url)
        if row is None:
            return headers
        h = dict(headers)
        if row.etag:
            h["If-None-Match"] = row.etag
        if row.last_modified:
            h["If-Modified-Since"] = row.last_modified
        return h

    def _persist_cache(self, url: str, r: requests.Response) -> None:
        pass  # as hash always change, cache is ineffective now
        # self._cache.upsert(
        #     url=url,
        #     etag=r.headers.get("ETag"),
        #     last_modified=r.headers.get("Last-Modified"),
        #     body=r.content,
        # )

    # ---------- API do port ----------
    def fetch(self, url: str, headers: dict[str, str] | None = None) -> bytes:
        with self.borrow_session() as s:
            return self.fetch_with(s, url, headers=headers)

    def fetch_with(self, session: Any, url: str, headers: dict[str, str] | None = None) -> bytes:
        # novo sorteio a cada tentativa para reduzir fingerprint
        attempts = 0
        last_exc: Exception | None = None
        while attempts < self._cfg.max_attempts:
            attempts += 1
            req_headers = self._pool.sample()
            if headers:
                req_headers.update(headers)
            req_headers = self._apply_conditional_headers(url, req_headers)
            try:
                r = session.get(url, headers=req_headers, timeout=self._cfg.timeout, allow_redirects=True)
                if r.status_code == 304:
                    row = self._cache.get(url)
                    if row and row.body is not None:
                        return row.body
                r.raise_for_status()
                # self._persist_cache(url, r)  # as hash always change, cache is ineffective now

                return r.content
            except requests.RequestException as e:  # noqa: PERF203
                last_exc = e
                # backoff local além do Retry do adapter
                sleep_expo_jitter(attempts)
        # se esgotou as tentativas, propaga a última exceção
        if last_exc:
            raise last_exc
        raise RuntimeError("unexpected http retry loop exit")

    @contextmanager
    def borrow_session(self) -> Iterator[requests.Session]:
        s = self._create_session()
        try:
            yield s
        finally:
            s.close()
