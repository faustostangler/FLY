from __future__ import annotations

from dataclasses import dataclass, field

from legacy.infrastructure.config.database import DatabaseConfig, load_database_config
from legacy.infrastructure.config.domain import DomainConfig, load_domain_config
from legacy.infrastructure.config.exchange_api import (
    ExchangeApiConfig,
    load_exchange_api_config,
)
from legacy.infrastructure.config.global_settings import (
    GlobalSettingsConfig,
    load_global_settings_config,
)
from legacy.infrastructure.config.http import HttpConfig, load_http_config
from legacy.infrastructure.config.logging import LoggingConfig, load_logging_config
from legacy.infrastructure.config.paths import PathConfig, load_paths
from legacy.infrastructure.config.scraping import ScrapingConfig, load_scraping_config
from legacy.infrastructure.config.statements import (
    StatementsConfig,
    load_statements_config,
)
from legacy.infrastructure.config.transformers import (
    TransformersConfig,
    load_transformers_config,
)


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
