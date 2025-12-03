from __future__ import annotations

import random
import ssl
import time
from typing import TYPE_CHECKING, Optional, Protocol, cast
from wsgiref import headers

import certifi
import cloudscraper
import requests
import urllib3
from requests.adapters import HTTPAdapter
from requests.structures import CaseInsensitiveDict

from domain.ports import ConfigPort, LoggerPort
from infrastructure.helpers.time_utils import TimeUtils
from infrastructure.utils.id_generator import IdGenerator

if TYPE_CHECKING:

    class ScrapingConfigProtocol(Protocol):
        user_agents: list[str]
        referers: list[str]
        languages: list[str]
        test_internet: Optional[str]
        timeout: Optional[int]

    class ConfigWithScraping(ConfigPort, Protocol):
        scraping: ScrapingConfigProtocol


class FetchUtils:
    """Utility class for HTTP operations with retry and randomized headers."""

    def __init__(self, config: ConfigPort, logger: LoggerPort) -> None:
        self.config = config
        self.logger = logger
        self.time_util = TimeUtils(self.config)

        self.id_generator = IdGenerator(config=config)

        # self.logger.log(f"Load Class {self.__class__.__name__}", level="info")

    def _scraping(self) -> "ScrapingConfigProtocol":
        return cast("ConfigWithScraping", self.config).scraping

    def header_random(self) -> dict:
        """Generate random HTTP headers based on scraping config."""
        try:
            cfg = self._scraping()
            return {
                "User-Agent": random.choice(cfg.user_agents),
                "Referer": random.choice(cfg.referers),
                "Accept-Language": random.choice(cfg.languages),
            }
        except Exception:
            return {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
                "Referer": "https://www.google.com/",
                "Accept-Language": "en-US,en;q=0.9",
            }

    def create_scraper_old(self, insecure: bool = False) -> requests.Session:
        """Return a configured requests session.

        Args:
            insecure: Whether to disable SSL verification.

        Returns:
            Configured ``requests.Session`` instance.
        """
        self.test_internet()

        session = requests.Session()
        session.trust_env = False
        session.headers = CaseInsensitiveDict()

        headers = self.header_random()
        session.headers.update(headers)

        if insecure:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            class InsecureAdapter(HTTPAdapter):
                def init_poolmanager(self, *args, **kwargs) -> None:
                    kwargs["ssl_context"] = context
                    self.poolmanager = urllib3.poolmanager.PoolManager(*args, **kwargs)

            session.mount("https://", InsecureAdapter())
            session.verify = False
        else:
            session.verify = certifi.where()

        return session

    def create_scraper(self, insecure: bool = False) -> requests.Session:
        """Return a configured cloudscraper session.

        Args:
            insecure: Whether to disable SSL verification.

        Returns:
            Configured ``requests.Session`` instance.
        """
        self.test_internet()

        headers = self.header_random()
        # Fewer TCP teardowns; plays nicer with anti-bot heuristics
        headers["Connection"] = "keep-alive"

        if insecure:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            class InsecureAdapter(HTTPAdapter):
                def init_poolmanager(self, *args, **kwargs) -> None:
                    kwargs["ssl_context"] = context
                    self.poolmanager = urllib3.poolmanager.PoolManager(*args, **kwargs)

            base_session = requests.Session()
            base_session.mount("https://", InsecureAdapter())
            base_session.headers = CaseInsensitiveDict()
            base_session.headers.update(headers)
            base_session.trust_env = False

            scraper = cloudscraper.create_scraper(sess=base_session)
            scraper.verify = False
        else:
            scraper = cloudscraper.create_scraper()
            scraper.headers = CaseInsensitiveDict()
            scraper.headers.update(headers)
            scraper.trust_env = False
            scraper.verify = certifi.where()

        return scraper

    def test_internet(
        self, url: Optional[str] = None, timeout: Optional[int] = None
    ) -> bool:
        """Checks if internet connection is active via HTTP GET request."""
        cfg = self._scraping()
        url = url or cfg.test_internet or "https://www.google.com"
        timeout = timeout or cfg.timeout or 5

        while True:
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200 or response.status_code == 204:
                    return True
            except Exception:
                # não faz nada, apenas dorme e tenta de novo
                url = "https://www.google.com"
                pass

            # aguarda um intervalo antes da próxima tentativa
            self.time_util.sleep_dynamic()

    def fetch_with_retry(
        self,
        scraper: Optional[requests.Session],
        url: str,
        cache_bypass: bool = True,
        timeout: Optional[int] = None,
        insecure: bool = False,
        worker_id: Optional[str] = None,
    ) -> tuple[requests.Response, requests.Session]:
        """Fetch a URL, recreating the scraper when blocked."""

        cfg = self._scraping()
        timeout = timeout or cfg.timeout or 5
        scraper = scraper or self.create_scraper(insecure=insecure)

        block_start = None
        attempt = 0

        while True:
            try:
                if cache_bypass:
                    # random parameter for no-cache, encoding is just for fun
                    param_name = self.id_generator.create_id(random.randint(1, 4))
                    digest = self.id_generator.create_id(random.randint(4, 12))
                    no_cache = f"{param_name}={digest}"
                    url = f"{url}&{no_cache}"

                # Perform the request with the current session
                timeout_wait = timeout + attempt
                response = scraper.get(url, timeout=timeout_wait)
                size = len(response.content)
                atmpt = 0
                dur = 0

                while size == 0:
                    atmpt += 1
                    start_time = time.perf_counter()
                    response = scraper.get(url, timeout=timeout_wait)
                    size = len(response.content)
                    self.time_util.sleep_dynamic(multiplier=atmpt)
                    end_time = time.perf_counter() - start_time
                    dur += end_time
                    self.logger.log(
                        f"Retry {atmpt + 1}: {response.status_code}, {end_time:.2f}s, {dur:.2f}s"
                    )

                if response.status_code == 200:
                    # On success, log the total block time if any
                    if block_start:
                        _block_duration = time.perf_counter() - block_start
                        # self.logger.log(
                        #     f"Dodging server block: {block_duration:.2f}s",
                        #     level="warning",
                        #     worker_id=worker_id,
                        # )
                    return response, scraper
            except (requests.Timeout, requests.ConnectionError):
                if not self.test_internet():
                    continue

            except Exception:  # noqa: BLE001
                # Ignore network errors and retry with a new scraper
                pass
                self.logger.log(
                    f"Attempt {attempt + 1} {url}", level="warning", worker_id=worker_id
                )

            # Record the start of blocking period on first failure
            if block_start is None:
                block_start = time.perf_counter()

            attempt += 1
            # Wait using dynamic sleep to avoid aggressive retries
            self.time_util.sleep_dynamic(multiplier=attempt)

            # Recreate the scraper session in case we were blocked
            scraper = self.create_scraper(insecure=insecure)

            # self.logger.log("Recreating scraper due to block", level="info")
