from __future__ import annotations

from dataclasses import dataclass, field

from infrastructure.config.cache import CachePolicy
from infrastructure.config.database import DatabaseConfig, load_database_config
from infrastructure.config.domain import DomainConfig, load_domain_config
from infrastructure.config.exchange_api import ExchangeApiConfig, load_exchange_api_config
from infrastructure.config.fly_settings import FlyConfig, load_fly_config
from infrastructure.config.logger import LoggerConfig, load_logger_config
from infrastructure.config.paths import PathConfig, load_paths
from infrastructure.config.repository import RepositoryConfig, load_repository_config
from infrastructure.config.scraping import ScrapingConfig, load_scraping_config
from infrastructure.config.statements import StatementsConfig, load_statements_config
from infrastructure.config.worker_pool import WorkerPoolConfig, load_worker_pool_config


@dataclass(frozen=True)
class ConfigAdapter:
    """Aggregate all application configurations.

    Provides centralized access to settings for paths, database connections,
    logging, domain rules, scraping, repositories, external APIs, and worker
    pools. Each field is constructed via its corresponding factory.
    """

    # Core filesystem paths used by the application (root, logs, data, temp)
    paths: PathConfig = field(default_factory=load_paths)

    # Application identity and runtime environment features
    fly_settings: FlyConfig = field(default_factory=load_fly_config)

    # Database connection and persistence settings
    database: DatabaseConfig = field(default_factory=load_database_config)

    # Logging configuration (format, level, sinks)
    logging: LoggerConfig = field(default_factory=load_logger_config)

    # Domain-specific business logic and validation rules
    domain: DomainConfig = field(default_factory=load_domain_config)

    # Default scraping parameters (timeouts, retries, HTTP headers)
    scraping: ScrapingConfig = field(default_factory=load_scraping_config)

    # Repository persistence policies (batch sizes, thresholds)
    repository: RepositoryConfig = field(default_factory=load_repository_config)

    # External stock exchange API endpoints and localization options
    exchange: ExchangeApiConfig = field(default_factory=load_exchange_api_config)

    # Worker pool sizing and concurrency limits
    worker_pool: WorkerPoolConfig = field(default_factory=load_worker_pool_config)

    # Statements to Scrape
    statements: StatementsConfig = field(default_factory=load_statements_config)

    # Ratios cache configuration (paths, eviction thresholds)
    cache: CachePolicy = CachePolicy()

