"""Public interface for infrastructure configuration adapters."""

from .adapter import ConfigAdapter

# Backward-compatible alias expected by some tests
Config = ConfigAdapter

__all__ = ["ConfigAdapter", "Config"]
