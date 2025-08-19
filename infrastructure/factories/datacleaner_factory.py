from __future__ import annotations

from domain.ports import ConfigPort, LoggerPort
from infrastructure.adapters.datacleaner_adapter import DataCleaner


def datacleaner_factory(config: ConfigPort, logger: LoggerPort) -> DataCleaner:
    """Factory that builds a ready-to-use ``DataCleaner`` instance."""
    return DataCleaner(config, logger)

