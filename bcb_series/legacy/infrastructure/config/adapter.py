from __future__ import annotations

from dataclasses import dataclass, field

from .database import DatabaseConfig, load_database_config
from .domain import DomainConfig, load_domain_config
from .exchange_api import ExchangeApiConfig, load_exchange_api_config
from .global_settings import GlobalSettingsConfig, load_global_settings_config
from .http import HttpConfig, load_http_config
from .logging import LoggingConfig, load_logging_config
from .paths import PathConfig, load_paths
from .scraping import ScrapingConfig, load_scraping_config
from .statements import StatementsConfig, load_statements_config
from .transformers import TransformersConfig, load_transformers_config


@dataclass(frozen=True)
class ConfigAdapter:
    """Aggregate configuration composed of individual sections."""

    paths: PathConfig = field(default_factory=load_paths)
    database: DatabaseConfig = field(default_factory=load_database_config)
    exchange: ExchangeApiConfig = field(default_factory=load_exchange_api_config)
    scraping: ScrapingConfig = field(default_factory=load_scraping_config)
    logging: LoggingConfig = field(default_factory=load_logging_config)
    global_settings: GlobalSettingsConfig = field(
        default_factory=load_global_settings_config
    )
    domain: DomainConfig = field(default_factory=load_domain_config)
    statements: StatementsConfig = field(default_factory=load_statements_config)
    transformers: TransformersConfig = field(default_factory=load_transformers_config)
    http: HttpConfig = field(default_factory=load_http_config)
