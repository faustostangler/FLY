from __future__ import annotations

from typing import Protocol, Sequence


class GlobalSettingsPort(Protocol):
    """Minimal subset of global runtime settings used by the application."""

    max_workers: int
    # Optional additional settings like batch_size can be added here


class DomainConfigPort(Protocol):
    """Domain-specific configuration values."""

    statements_types: Sequence[str]


class TransformersConfigPort(Protocol):
    """Configuration for statement transformers."""

    math_target_accounts: Sequence[str]


class ConfigPort(Protocol):
    """Structural contract for configuration objects used across layers."""

    global_settings: GlobalSettingsPort
    domain: DomainConfigPort
    transformers: TransformersConfigPort
    # Additional sections can be included as needed
