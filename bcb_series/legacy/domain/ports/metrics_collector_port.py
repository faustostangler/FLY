"""Port for collecting metrics from scraping and processing."""

from __future__ import annotations

from typing import Protocol

from domain.dto import MetricsDTO


class MetricsCollectorPort(Protocol):
    """Collects and exposes metrics for network and processing byte counts."""

    def record_network_bytes(self, n: int) -> None:
        """Accumulate ``n`` bytes transferred over the network."""
        raise NotImplementedError

    def record_processing_bytes(self, n: int) -> None:
        """Accumulate ``n`` bytes processed locally."""
        raise NotImplementedError

    @property
    def network_bytes(self) -> int:
        """Total bytes transferred over the network."""
        raise NotImplementedError

    @property
    def processing_bytes(self) -> int:
        """Total bytes processed locally."""
        raise NotImplementedError

    def get_metrics(self, elapsed_time: float) -> MetricsDTO:
        """Return collected metrics as a DTO."""
        raise NotImplementedError
