from domain.dto import MetricsDTO
from domain.ports import MetricsCollectorPort


class MetricsCollector(MetricsCollectorPort):
    """Collects network and processing byte counts."""

    def __init__(self) -> None:
        """Initialize counters to zero."""

        self._network_bytes = 0
        self._processing_bytes = 0

    def record_network_bytes(self, n: int) -> None:
        """Accumulate ``n`` bytes transferred over the network."""

        self._network_bytes += n

    def record_processing_bytes(self, n: int) -> None:
        """Accumulate ``n`` bytes processed locally."""

        self._processing_bytes += n

    @property
    def network_bytes(self) -> int:
        """Return the total network bytes."""

        return self._network_bytes

    @property
    def processing_bytes(self) -> int:
        """Return the total processing bytes."""

        return self._processing_bytes

    def get_metrics(self, elapsed_time: float) -> MetricsDTO:
        """Create a :class:`MetricsDTO` instance from the collected values."""

        return MetricsDTO(
            elapsed_time=elapsed_time,
            network_bytes=self._network_bytes,
            processing_bytes=self._processing_bytes,
        )
