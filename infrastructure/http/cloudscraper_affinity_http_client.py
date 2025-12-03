# infrastructure/http/cloudscraper_affinity_http_client.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

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


class CloudscraperAffinityHttpClient(AffinityHttpClientPort, EngineSetup):
    """Cliente HTTP com Cloudscraper, randomização de headers, pool, retries e backoff."""

    def __init__(self, connection_string: str, logger: LoggerPort) -> None:
        EngineSetup.__init__(self, connection_string, logger)
        self._cfg = load_scraping_config()
        self._pool = HeadersPool.from_config()

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
            try:
                r = session.get(url, headers=req_headers, timeout=self._cfg.timeout, allow_redirects=True)
                r.raise_for_status()

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
