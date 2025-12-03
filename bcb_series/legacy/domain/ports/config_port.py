from __future__ import annotations

from typing import Mapping, Protocol, Sequence, runtime_checkable


@runtime_checkable
class DatabaseConfigPort(Protocol):
    """Database configuration values required by infrastructure."""

    @property
    def connection_string(self) -> str: ...

    @property
    def tables(self) -> Mapping[str, str]: ...


@runtime_checkable
class GlobalSettingsPort(Protocol):
    """Minimal subset of global runtime settings used by the application."""

    @property
    def app_name(self) -> str: ...

    @property
    def wait(self) -> int: ...

    @property
    def threshold(self) -> int: ...

    @property
    def max_linear_holes(self) -> int: ...

    @property
    def max_workers(self) -> int: ...

    @property
    def batch_size(self) -> int: ...

    @property
    def queue_size(self) -> int: ...

    @property
    def request_timeout_sec(self) -> float: ...

    @property
    def user_agent(self) -> str: ...


@runtime_checkable
class DomainConfigPort(Protocol):
    """Domain-specific configuration values."""

    @property
    def base_currency(self) -> str: ...

    @property
    def nsd_gap_days(self) -> int: ...

    @property
    def words_to_remove(self) -> Sequence[str]: ...

    @property
    def statements_types(self) -> Sequence[str]: ...


@runtime_checkable
class TransformersConfigPort(Protocol):
    """Configuration for statement transformers."""

    @property
    def enabled(self) -> Mapping[str, bool]: ...

    @property
    def order(self) -> Sequence[str]: ...

    @property
    def math_year_end_prefixes(self) -> Sequence[str]: ...

    @property
    def math_cumulative_prefixes(self) -> Sequence[str]: ...

    @property
    def math_target_accounts(self) -> Sequence[str]: ...

    @property
    def intel_year_end_prefixes(self) -> Sequence[str]: ...

    @property
    def intel_cumulative_prefixes(self) -> Sequence[str]: ...

    # @property
    # def intel_section_criteria(
    #     self,
    # ) -> Sequence[tuple[str, Sequence[dict[str, object]]]]: ...
    @property
    def intel_section_criteria(
        self,
    ) -> Sequence[tuple[str, Sequence[dict[str, object]]]]: ...


@runtime_checkable
class ExchangeApiConfigPort(Protocol):
    """API endpoints used for scraping exchange data."""

    @property
    def nsd_endpoint(self) -> str: ...

    @property
    def company_data_endpoint(self) -> Mapping[str, str]: ...

    @property
    def language(self) -> str: ...


@runtime_checkable
class StatementsConfigPort(Protocol):
    """Configuration values for fetching statement pages."""

    @property
    def statement_items(self) -> Sequence[Mapping[str, object]]: ...

    @property
    def nsd_type_map(self) -> Mapping[str, tuple[str, int]]: ...

    @property
    def capital_items(self) -> Sequence[Mapping[str, str]]: ...

    @property
    def url_df(self) -> str: ...

    @property
    def url_capital(self) -> str: ...


@runtime_checkable
class HttpConfigPort(Protocol):
    @property
    def session_pool_size(self) -> int: ...
    
    @property
    def timeout_connect(self) -> float: ...
    
    @property
    def timeout_read(self) -> float: ...
    
    @property
    def rate_per_sec(self) -> float: ...
    
    @property
    def burst(self) -> int: ...
    
    @property
    def circuit_failures(self) -> int: ...
    
    @property
    def circuit_open_seconds(self) -> float: ...
    
    @property
    def retries(self) -> int: ...
    
    @property
    def backoff_factor(self) -> float: ...
    
    @property
    def status_forcelist(self) -> list[int]: ...
    
    @property
    def respect_retry_after_header(self) -> bool: ...
    
    @property
    def pool_connections(self) -> int: ...
    
    @property
    def pool_maxsize(self) -> int: ...


@runtime_checkable
class ConfigPort(Protocol):
    """Structural contract for configuration objects used across layers."""

    @property
    def global_settings(self) -> GlobalSettingsPort: ...

    @property
    def domain(self) -> DomainConfigPort: ...

    @property
    def transformers(self) -> TransformersConfigPort: ...

    @property
    def database(self) -> DatabaseConfigPort: ...

    @property
    def exchange(self) -> ExchangeApiConfigPort: ...

    @property
    def statements(self) -> StatementsConfigPort: ...

    @property
    def http(self) -> HttpConfigPort: ...


__all__ = [
    "ConfigPort",
    "GlobalSettingsPort",
    "DomainConfigPort",
    "TransformersConfigPort",
    "DatabaseConfigPort",
    "ExchangeApiConfigPort",
    "StatementsConfigPort",
    "HttpConfigPort",
]
