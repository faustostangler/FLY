# infrastructure/http/metrics_http_client.py
from __future__ import annotations

from typing import Any, ContextManager

from application.ports.http_client_port import AffinityHttpClientPort
from application.ports.metrics_collector_port import MetricsCollectorPort


class MetricsHttpClient(AffinityHttpClientPort):
    def __init__(self, inner: AffinityHttpClientPort, metrics: MetricsCollectorPort) -> None:
        self._inner = inner
        self._metrics = metrics

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> bytes:
        body = self._inner.fetch(url, headers=headers)
        download_size = len(body)
        self._metrics.add_network_bytes(download_size)
        return body

    def fetch_with(self, session: Any, url: str, headers: dict[str, str] | None = None) -> bytes:
        body = self._inner.fetch_with(session, url, headers=headers)
        download_size = len(body)
        self._metrics.add_network_bytes(download_size)
        return body

    def borrow_session(self) -> ContextManager[Any]:
        return self._inner.borrow_session()
