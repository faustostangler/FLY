from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class MetricsCollectorPort(Protocol):
    """Protocol defining a contract for collecting network byte metrics.

    Any implementing class must provide a method to add network bytes
    and a property to expose the current total of collected bytes.
    """

    def add_network_bytes(self, n: int) -> None:
        """Add a number of bytes to the network metrics counter.

        Args:
            n (int): Number of bytes to add.
        """
        ...

    @property
    def network_bytes(self) -> int:
        """Retrieve the current total of collected network bytes.

        Returns:
            int: The accumulated number of network bytes.
        """
        ...

    @property
    def download_bytes(self) -> int:
        """Retrieve the current size of collected download bytes.

        Returns:
            int: The accumulated number of download bytes.
        """
        ...
