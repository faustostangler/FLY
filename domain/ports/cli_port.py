from typing import Protocol


class CliPort(Protocol):
    def start_fly(self) -> None:
        """Start the FLY application from CLI interface."""
        ...
