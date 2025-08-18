from typing import Protocol, runtime_checkable


@runtime_checkable
class MetricsCollectorPort(Protocol):
    """Port for collecting network byte metrics only."""

    def add_network_bytes(self, n: int) -> None: ...

    @property
    def network_bytes(self) -> int: ...
