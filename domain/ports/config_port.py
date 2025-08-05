"""Configuration port definitions."""

from __future__ import annotations

from typing import Iterable, Protocol


class DomainConfigPort(Protocol):
    """Port for domain-specific configuration values."""

    statements_types: Iterable[str]


class GlobalSettingsConfigPort(Protocol):
    """Port for global settings configuration values."""

    threshold: int
    max_workers: int | None
    queue_size: int


class TransformersConfigPort(Protocol):
    """Port for transformer-related configuration values."""

    math_target_accounts: Iterable[str]


class ConfigPort(Protocol):
    """Aggregate configuration port exposing nested config sections."""

    domain: DomainConfigPort
    global_settings: GlobalSettingsConfigPort
    transformers: TransformersConfigPort
