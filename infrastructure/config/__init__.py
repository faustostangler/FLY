"""Public interface for infrastructure configuration adapters."""

from .adapter import ConfigAdapter

# Backwards compatibility alias
Config = ConfigAdapter

__all__ = ["ConfigAdapter", "Config"]
