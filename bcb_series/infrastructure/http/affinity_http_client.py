from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import requests


class RequestsAffinityHttpClient:
    """HTTP client wrapper with built-in timeout and optional session reuse.

    Provides convenience methods for performing HTTP GET requests,
    with or without a persistent `requests.Session`, and ensures
    response validation.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize the HTTP client with a default timeout.

        Args:
            timeout (float): Maximum number of seconds to wait for
                a response before raising a timeout error.
                Defaults to 30.0 seconds.
        """
        # Request timeout applied to all GET calls
        self._timeout = timeout

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> bytes:
        """Perform a GET request without session reuse.

        Args:
            url (str): The target URL.
            headers (dict[str, str] | None): Optional request headers.

        Returns:
            bytes: The response body content.

        Raises:
            requests.HTTPError: If the response contains a non-2xx status code.
        """
        # One-off GET request (no persistent session)
        r = requests.get(url, headers=headers, timeout=self._timeout, allow_redirects=True)
        r.raise_for_status()
        return r.content

    def fetch_with(self, session: requests.Session, url: str, headers: dict[str, str] | None = None) -> bytes:
        """Perform a GET request using an existing session.

        Args:
            session (requests.Session): Reusable session for HTTP requests.
            url (str): The target URL.
            headers (dict[str, str] | None): Optional request headers.

        Returns:
            bytes: The response body content.

        Raises:
            requests.HTTPError: If the response contains a non-2xx status code.
        """
        # GET request leveraging a provided session
        r = session.get(url, headers=headers, timeout=self._timeout, allow_redirects=True)
        r.raise_for_status()
        return r.content

    @contextmanager
    def borrow_session(self) -> Iterator[requests.Session]:
        """Context manager that provides a temporary `requests.Session`.

        Yields:
            Iterator[requests.Session]: A session object that is
            automatically closed when the context exits.
        """
        # Open a temporary session and ensure cleanup after use
        with requests.Session() as s:
            yield s
