# application/ports/config_port.py

from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Protocol, Tuple, runtime_checkable


# Defines the filesystem path contract that implementations must provide
@runtime_checkable
class PathConfigPort(Protocol):
    """Contract for path-related configuration."""

    @property
    def temp_dir(self) -> Path: ...
    @property
    def log_dir(self) -> Path: ...
    @property
    def data_dir(self) -> Path: ...
    @property
    def cache_dir(self) -> Path: ...
    @property
    def root_dir(self) -> Path: ...


# Describes cache storage settings (location, eviction thresholds)
@runtime_checkable
class CacheConfigPort(Protocol):
    """Contract for cache configuration."""

    @property
    def max_cache_size_bytes(self) -> int: ...
    @property
    def max_age_days(self) -> int: ...
    @property
    def max_age(self) -> timedelta: ...
    @property
    def parquet_compression(self) -> str: ...


# Declares application identity and runtime flags exposed to the UI/CLIs
@runtime_checkable
class FlyConfigPort(Protocol):
    """Contract for application identity and runtime feature flags."""

    @property
    def app_name(self) -> str: ...
    @property
    def version(self) -> str: ...
    @property
    def show_path(self) -> bool: ...


# Exposes database connectivity and table naming conventions
@runtime_checkable
class DatabaseConfigPort(Protocol):
    """Contract for database configuration and connection details."""

    @property
    def db_filename(self) -> str: ...
    @property
    def db_cache_filename(self) -> str: ...
    @property
    def connection_string(self) -> str: ...
    @property
    def connection_cache_string(self) -> str: ...
    @property
    def tables(self) -> Mapping[str, str]: ...


# Controls logging output: where, how, and how much to log
@runtime_checkable
class LoggerConfigPort(Protocol):
    """Contract for logging configuration."""

    @property
    def log_dir(self) -> Path: ...
    @property
    def log_file_name(self) -> str: ...
    @property
    def level(self) -> str: ...
    @property
    def show_path(self) -> bool: ...


# Encapsulates business rules and domain-wide defaults
@runtime_checkable
class DomainConfigPort(Protocol):
    """Contract for domain-specific rules and defaults."""

    @property
    def words_to_remove(self) -> Tuple[str, ...]: ...
    @property
    def statements_types(self) -> Tuple[str, ...]: ...
    @property
    def base_currency(self) -> str: ...
    @property
    def nsd_gap_days(self) -> int: ...
    @property
    def recency_year(self) -> int: ...  # novo campo para NsdPolicy


@runtime_checkable
class ScrapingConfig(Protocol):
    """Contract for web scraping configuration."""

    @property
    def user_agents(self) -> List[str]: ...
    @property
    def referers(self) -> List[str]: ...
    @property
    def languages(self) -> List[str]: ...
    @property
    def test_internet(self) -> str: ...
    @property
    def timeout(self) -> int: ...
    @property
    def max_attempts(self) -> int: ...
    @property
    def linear_holes(self) -> int: ...


# Defines batching and durability thresholds for repositories
@runtime_checkable
class RepositoryConfig(Protocol):
    """Contract for repository batching and persistence thresholds."""

    @property
    def batch_size(self) -> int: ...
    @property
    def persistence_threshold(self) -> int: ...


# Describes external market data endpoints and localization
@runtime_checkable
class ExchangeApiConfig(Protocol):
    """Contract for stock exchange API configuration."""

    @property
    def language(self) -> str: ...
    @property
    def company_data_endpoint(self) -> Mapping[str, str]: ...
    @property
    def nsd_endpoint(self) -> str: ...


# Governs concurrency and queueing for local worker pools
@runtime_checkable
class WorkerPoolConfig(Protocol):
    """Contract for worker pool sizing and queue limits."""

    @property
    def max_workers(self) -> int: ...
    @property
    def queue_size(self) -> int: ...


@runtime_checkable
class StatementsConfigPort(Protocol):
    @property
    def statement_items(self) -> Tuple[Dict[str, Optional[int | str]], ...]: ...
    @property
    def nsd_type_map(self) -> Mapping[str, Tuple[str, int]]: ...
    @property
    def capital_items(self) -> List[Dict[str, str]]: ...
    @property
    def url_df(self) -> str: ...
    @property
    def url_capital(self) -> str: ...


# Aggregates all configuration ports into a single access surface
@runtime_checkable
class ConfigPort(Protocol):
    """High-level configuration contract that aggregates all sub-configs."""

    @property
    def paths(self) -> PathConfigPort: ...
    @property
    def fly_settings(self) -> FlyConfigPort: ...
    @property
    def database(self) -> DatabaseConfigPort: ...
    @property
    def logging(self) -> LoggerConfigPort: ...
    @property
    def scraping(self) -> ScrapingConfig: ...
    @property
    def domain(self) -> DomainConfigPort: ...
    @property
    def repository(self) -> RepositoryConfig: ...
    @property
    def exchange(self) -> ExchangeApiConfig: ...
    @property
    def worker_pool(self) -> WorkerPoolConfig: ...
    @property
    def statements(self) -> StatementsConfigPort: ...
    @property
    def cache(self) -> CacheConfigPort: ...
