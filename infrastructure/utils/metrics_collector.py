from domain.ports.metrics_collector_port import MetricsCollectorPort


class MetricsCollector(MetricsCollectorPort):
    """Simple implementation of a metrics collector.

    Tracks only the total number of bytes transferred over the network.
    """

    def __init__(self) -> None:
        # Internal counter for accumulated network bytes
        self._network_bytes = 0

    def add_network_bytes(self, n: int) -> None:
        """Accumulate bytes transferred over the network.

        Args:
            n (int): Number of bytes to add to the running total.
        """
        self._network_bytes += n

    @property
    def network_bytes(self) -> int:
        """Get the total number of network bytes collected.

        Returns:
            int: The accumulated network byte count.
        """
        return self._network_bytes
