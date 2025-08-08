"""Port definition for domain configuration settings."""

from __future__ import annotations

from typing import Protocol, Tuple


class DomainConfigPort(Protocol):
    """Expose domain-level configuration values."""

    words_to_remove: Tuple[str, ...]
    statements_types: Tuple[str, ...]
