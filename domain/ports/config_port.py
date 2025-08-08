"""Aggregate protocol for application configuration."""

from __future__ import annotations

from typing import Protocol

from .domain_config_port import DomainConfigPort
from .global_settings_config_port import GlobalSettingsConfigPort
from .transformers_config_port import TransformersConfigPort


class ConfigPort(Protocol):
    """Expose configuration sections required by the application."""

    domain: DomainConfigPort
    global_settings: GlobalSettingsConfigPort
    transformers: TransformersConfigPort
