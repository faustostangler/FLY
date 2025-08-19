from domain.ports.metrics_collector_port import MetricsCollectorPort


class MetricsCollector(MetricsCollectorPort):
    """Collects only the number of bytes transferred over the network."""

    def __init__(self) -> None:
        self._network_bytes = 0

    def add_network_bytes(self, n: int) -> None:
        """Accumulate ``n`` bytes transferred over the network."""
        self._network_bytes += n

    @property
    def network_bytes(self) -> int:
        """Return the total network bytes."""
        return self._network_bytes
