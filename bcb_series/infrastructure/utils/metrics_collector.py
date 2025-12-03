from application.ports.metrics_collector_port import MetricsCollectorPort


class MetricsCollector(MetricsCollectorPort):
    """Simple implementation of a metrics collector.

    Tracks only the total number of bytes transferred over the network.
    """

    def __init__(self) -> None:
        # Internal counter for accumulated network bytes
        self._network_bytes = 0
        self._download_bytes = 0

    def add_network_bytes(self, n: int) -> None:
        """Update network traffic counters.

        This method increments the total network bytes with the given value,
        while also setting the download bytes to the most recent increment.

        Args:
            n (int): Number of bytes transferred in the latest download.
                    Added to the total, and stored as the last download size.
        """
        self._download_bytes = n
        self._network_bytes += n

    @property
    def network_bytes(self) -> int:
        """Get the total number of network bytes collected.

        Returns:
            int: The accumulated network byte count.
        """
        return self._network_bytes

    @property
    def download_bytes(self) -> int:
        """Get the total number of download bytes collected.

        Returns:
            int: The accumulated download byte count.
        """
        return self._download_bytes
