from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CliPort(Protocol):
    """Protocol for CLI entry points of the application.

    Defines the interface that any CLI adapter must implement
    to start the FLY application.
    """

    def start_fly(self) -> None:
        """Start the FLY application from the CLI interface."""
        ...
