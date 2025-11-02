"""Public interface for infrastructure configuration adapters."""

from legacy.infrastructure.config.adapter import ConfigAdapter

# Backward-compatible alias expected by some tests
Config = ConfigAdapter

__all__ = ["ConfigAdapter", "Config"]
