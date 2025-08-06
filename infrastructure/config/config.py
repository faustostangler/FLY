"""Pure configuration DTO definitions."""

from dataclasses import dataclass

from .database import DatabaseConfig
from .domain import DomainConfig
from .exchange_api import ExchangeApiConfig
from .global_settings import GlobalSettingsConfig
from .logging import LoggingConfig
from .paths import PathConfig
from .scraping import ScrapingConfig
from .statements import StatementsConfig
from .transformers import TransformersConfig


@dataclass(frozen=True)
class Config:
    """Immutable aggregate of all configuration sections."""

    paths: PathConfig
    database: DatabaseConfig
    exchange: ExchangeApiConfig
    scraping: ScrapingConfig
    logging: LoggingConfig
    global_settings: GlobalSettingsConfig
    domain: DomainConfig
    statements: StatementsConfig
    transformers: TransformersConfig
