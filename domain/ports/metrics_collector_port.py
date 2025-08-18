from typing import Protocol


class MetricsCollectorPort(Protocol):
    """Port for collecting network byte metrics only."""

    def record_network_bytes(self, n: int) -> None:
        """Accumulate `n` bytes transferred over the network."""
        ...

    @property
    def network_bytes(self) -> int:
        """Return the total network bytes."""
        ...
