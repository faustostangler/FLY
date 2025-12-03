from __future__ import annotations

from typing import Any, ContextManager, Protocol


class AffinityHttpClientPort(Protocol):
    """Protocol definition for HTTP client implementations.

    Defines the expected interface for HTTP clients that support both
    direct fetching and session-based fetching, while providing a
    context manager for session lifecycle management.
    """

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> bytes:
        """Fetch content from a given URL without explicit session management.

        Args:
            url (str): Target URL to fetch.
            headers (dict[str, str] | None): Optional HTTP headers to include.

        Returns:
            bytes: Raw response body as bytes.
        """
        ...

    def fetch_with(
        self,
        session: Any,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        """Fetch content from a given URL using an existing session.

        Args:
            session (Any): Session object used to maintain connection state.
            url (str): Target URL to fetch.
            headers (dict[str, str] | None): Optional HTTP headers to include.

        Returns:
            bytes: Raw response body as bytes.
        """
        ...

    def borrow_session(self) -> ContextManager[Any]:
        """Provide a managed HTTP session via a context manager.

        Returns:
            ContextManager[Any]: A context manager yielding an HTTP session,
            ensuring proper creation and cleanup of resources.
        """
        ...
