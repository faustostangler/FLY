"""Pure configuration DTO definitions."""

from dataclasses import dataclass
from typing import Final

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

    paths: Final[PathConfig]
    database: Final[DatabaseConfig]
    exchange: Final[ExchangeApiConfig]
    scraping: Final[ScrapingConfig]
    logging: Final[LoggingConfig]
    global_settings: Final[GlobalSettingsConfig]
    domain: Final[DomainConfig]
    statements: Final[StatementsConfig]
    transformers: Final[TransformersConfig]
