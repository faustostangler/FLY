"""Aggregate configuration object that loads all config sections."""

from .database import DatabaseConfig, load_database_config
from .domain import DomainConfig, load_domain_config
from .exchange_api import ExchangeApiConfig, load_exchange_api_config
from .global_settings import GlobalSettingsConfig, load_global_settings_config
from .logging import LoggingConfig, load_logging_config
from .paths import PathConfig, load_paths
from .scraping import ScrapingConfig, load_scraping_config
from .statements import StatementsConfig, load_statements_config
from .transformers import (
    TransformersConfig,
    load_transformers_config,
)


class Config:
    """Aggregates all specialized configurations into a single object.

    Each attribute is an immutable and validated instance of its
    respective domain.
    """

    def __init__(self) -> None:
        """Run all configuration sections."""
        # Run all configurations
        self.paths: PathConfig = load_paths()
        self.database: DatabaseConfig = load_database_config()
        self.exchange: ExchangeApiConfig = load_exchange_api_config()
        self.scraping: ScrapingConfig = load_scraping_config()
        self.logging: LoggingConfig = load_logging_config()
        self.global_settings: GlobalSettingsConfig = load_global_settings_config()
        self.domain: DomainConfig = load_domain_config()
        self.statements: StatementsConfig = load_statements_config()
        self.transformers: TransformersConfig = load_transformers_config()
