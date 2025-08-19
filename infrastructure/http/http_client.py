# infrastructure/http/requests_affinity.py
from contextlib import contextmanager
from typing import Iterator

import requests


class RequestsAffinityHttpClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> bytes:
        r = requests.get(url, headers=headers, timeout=self._timeout, allow_redirects=True)
        r.raise_for_status()
        return r.content

    def fetch_with(self, session: requests.Session, url: str, headers: dict[str, str] | None = None) -> bytes:
        r = session.get(url, headers=headers, timeout=self._timeout, allow_redirects=True)
        r.raise_for_status()
        return r.content

    @contextmanager
    def borrow_session(self) -> Iterator[requests.Session]:
        with requests.Session() as s:
            yield s
