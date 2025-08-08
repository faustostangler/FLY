"""Port definition for global settings configuration."""

from __future__ import annotations

from typing import Protocol


class GlobalSettingsConfigPort(Protocol):
    """Expose application-wide configuration values."""

    app_name: str
    wait: int
    threshold: int
    max_linear_holes: int
    max_workers: int
    batch_size: int
    queue_size: int
