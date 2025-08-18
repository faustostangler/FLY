from typing import Protocol, runtime_checkable


@runtime_checkable
class CliPort(Protocol):
    def start_fly(self) -> None:
        """Start the FLY application from CLI interface."""
        ...
