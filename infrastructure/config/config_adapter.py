from __future__ import annotations

from dataclasses import dataclass, field

from .database import DatabaseConfig, load_database_config
from .domain import DomainConfig, load_domain_config
from .exchange_api import ExchangeApiConfig, load_exchange_api_config
from .fly_settings import FlyConfig, load_fly_config
from .logger import LoggerConfig, load_logger_config
from .paths import PathConfig, load_paths
from .repository import RepositoryConfig, load_repository_config
from .scraping import ScrapingConfig, load_scraping_config
from .worker_pool import WorkerPoolConfig, load_worker_pool_config

@dataclass(frozen=True)
class ConfigAdapter:
    paths: PathConfig = field(default_factory=load_paths)
    fly_settings: FlyConfig = field(default_factory=load_fly_config)
    database: DatabaseConfig = field(default_factory=load_database_config)
    logging: LoggerConfig = field(default_factory=load_logger_config)
    domain: DomainConfig = field(default_factory=load_domain_config)
    scraping: ScrapingConfig = field(default_factory=load_scraping_config)
    repository: RepositoryConfig = field(default_factory=load_repository_config)
    exchange: ExchangeApiConfig = field(default_factory=load_exchange_api_config)
    worker_pool: WorkerPoolConfig = field(default_factory=load_worker_pool_config)
