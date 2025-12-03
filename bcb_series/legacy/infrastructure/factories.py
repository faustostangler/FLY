from domain.ports import LoggerPort
from infrastructure.config import ConfigAdapter
from infrastructure.helpers.datacleaner import DataCleaner


def create_datacleaner(config: ConfigAdapter, logger: LoggerPort) -> DataCleaner:
    """Factory that builds a ready-to-use ``DataCleaner`` instance."""
    return DataCleaner(config, logger)
