from domain.ports import LoggerPort
from infrastructure.config import ConfigAdapter
from infrastructure.helpers.data_cleaner import DataCleaner


def create_data_cleaner(config: ConfigAdapter, logger: LoggerPort) -> DataCleaner:
    """Factory that builds a ready-to-use ``DataCleaner`` instance."""
    return DataCleaner(config, logger)
