from pathlib import Path
from typing import Dict, List, Mapping, Optional, Protocol, Tuple, runtime_checkable


# Defines the filesystem path contract that implementations must provide
@runtime_checkable
class PathConfigPort(Protocol):
    """Contract for path-related configuration."""

    @property
    def temp_dir(self) -> Path:
        """Temporary directory used for ephemeral files."""
        ...

    @property
    def log_dir(self) -> Path:
        """Directory where application logs are written."""
        ...

    @property
    def data_dir(self) -> Path:
        """Directory that stores application data artifacts."""
        ...

    @property
    def root_dir(self) -> Path:
        """Project/application root directory."""
        ...


# Declares application identity and runtime flags exposed to the UI/CLIs
@runtime_checkable
class FlyConfigPort(Protocol):
    """Contract for application identity and runtime feature flags."""

    @property
    def app_name(self) -> str:
        """Human-friendly application name."""
        ...

    @property
    def version(self) -> str:
        """Semantic version of the running application."""
        ...

    @property
    def show_path(self) -> bool:
        """Whether to include path information in outputs."""
        ...


# Exposes database connectivity and table naming conventions
@runtime_checkable
class DatabaseConfigPort(Protocol):
    """Contract for database configuration and connection details."""

    @property
    def db_filename(self) -> str:
        """Underlying database filename (e.g., SQLite file)."""
        ...

    @property
    def connection_string(self) -> str:
        """SQLAlchemy-style connection URI."""
        ...

    @property
    def tables(self) -> Mapping[str, str]:
        """Mapping of logical table keys to physical table names."""
        ...


# Controls logging output: where, how, and how much to log
@runtime_checkable
class LoggerConfigPort(Protocol):
    """Contract for logging configuration."""

    @property
    def log_dir(self) -> Path:
        """Directory where log files are stored."""
        ...

    @property
    def log_file_name(self) -> str:
        """Name of the primary log file."""
        ...

    @property
    def level(self) -> str:
        """Minimum log level (e.g., DEBUG, INFO)."""
        ...

    @property
    def show_path(self) -> bool:
        """Whether to include file path details in log messages."""
        ...


# Encapsulates business rules and domain-wide defaults
@runtime_checkable
class DomainConfigPort(Protocol):
    """Contract for domain-specific rules and defaults."""

    @property
    def words_to_remove(self) -> Tuple[str, ...]:
        """Stopwords or tokens to remove from inputs."""
        ...

    @property
    def statements_types(self) -> Tuple[str, ...]:
        """Accepted statement types within the domain."""
        ...

    @property
    def base_currency(self) -> str:
        """Canonical currency used for normalization."""
        ...

    @property
    def nsd_gap_days(self) -> int:
        """Minimum day gap used for NSD calculations."""
        ...


@runtime_checkable
class ScrapingConfig(Protocol):
    """Contract for web scraping configuration."""

    @property
    def user_agents(self) -> List[str]:
        """Filename of the JSON file containing user-agent strings."""
        ...

    @property
    def referers(self) -> List[str]:
        """Filename of the JSON file containing referer URLs."""
        ...

    @property
    def languages(self) -> List[str]:
        """Filename of the JSON file containing Accept-Language headers."""
        ...

    @property
    def test_internet(self) -> str:
        """URL used to verify internet connectivity."""
        ...

    @property
    def timeout(self) -> int:
        """Timeout in seconds for HTTP requests."""
        ...

    @property
    def max_attempts(self) -> int:
        """Maximum number of retry attempts per request."""
        ...

    @property
    def linear_holes(self) -> int:
        """Maximum number of linear holes allowed in the NSD scraping process."""
        ...

# Defines batching and durability thresholds for repositories
@runtime_checkable
class RepositoryConfig(Protocol):
    """Contract for repository batching and persistence thresholds."""

    @property
    def batch_size(self) -> int:
        """Preferred number of items processed per batch."""
        ...

    @property
    def persistence_threshold(self) -> int:
        """Count threshold that triggers persistence."""
        ...


# Describes external market data endpoints and localization
@runtime_checkable
class ExchangeApiConfig(Protocol):
    """Contract for stock exchange API configuration."""

    @property
    def language(self) -> str:
        """Preferred language for API requests/responses."""
        ...

    @property
    def company_data_endpoint(self) -> Mapping[str, str]:
        """Mapping of company data endpoints by provider or resource."""
        ...

    @property
    def nsd_endpoint(self) -> str:
        """Endpoint used to fetch NSD-related data."""
        ...


# Governs concurrency and queueing for local worker pools
@runtime_checkable
class WorkerPoolConfig(Protocol):
    """Contract for worker pool sizing and queue limits."""

    @property
    def max_workers(self) -> int:
        """Maximum number of concurrent worker threads/processes."""
        ...

    @property
    def queue_size(self) -> int:
        """Maximum number of pending tasks in the queue."""
        ...


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
    def paths(self) -> PathConfigPort:
        """Filesystem path configuration."""
        ...

    @property
    def fly_settings(self) -> FlyConfigPort:
        """Application identity and runtime flags."""
        ...

    @property
    def database(self) -> DatabaseConfigPort:
        """Database connection and table naming details."""
        ...

    @property
    def logging(self) -> LoggerConfigPort:
        """Logging output destination and verbosity."""
        ...

    @property
    def scraping(self) -> ScrapingConfig:
        """Domain-specific rules and defaults."""
        ...

    @property
    def domain(self) -> DomainConfigPort:
        """Domain-specific rules and defaults."""
        ...

    @property
    def repository(self) -> RepositoryConfig:
        """Repository batching and durability thresholds."""
        ...

    @property
    def exchange(self) -> ExchangeApiConfig:
        """External market data endpoints and localization."""
        ...

    @property
    def worker_pool(self) -> WorkerPoolConfig:
        """Local concurrency configuration for worker pools."""
        ...

    @property
    def statements(self) -> StatementsConfigPort: ...

# Encapsulates global settings used across various components