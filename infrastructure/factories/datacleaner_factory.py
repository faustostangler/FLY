from __future__ import annotations

from application.ports.config_port import ConfigPort
from application.ports.logger_port import LoggerPort
from infrastructure.adapters.datacleaner_adapter import DataCleaner


def datacleaner_factory(config: ConfigPort, logger: LoggerPort) -> DataCleaner:
    """Factory function to create a configured DataCleaner instance.

    Args:
        config (ConfigPort): Provides access to application configuration.
        logger (LoggerPort): Logging interface for monitoring and debugging.

    Returns:
        DataCleaner: A fully initialized DataCleaner instance ready for use.
    """
    # Build and return a DataCleaner wired with configuration and logging
    return DataCleaner(config, logger)
