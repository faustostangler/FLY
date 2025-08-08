"""Domain-level immutable configuration settings."""

from dataclasses import dataclass, field
from typing import Tuple

WORDS_TO_REMOVE: Tuple[str, ...] = (
    "EM LIQUIDACAO",
    "EM LIQUIDACAO EXTRAJUDICIAL",
    "EXTRAJUDICIAL",
    "EM RECUPERACAO JUDICIAL",
    "EM REC JUDICIAL",
    "EMPRESA FALIDA",
    "MASSA FALIDA DA",
)

STATEMENTS_TYPES: Tuple[str, ...] = (
    "DEMONSTRACOES FINANCEIRAS PADRONIZADAS",
    "INFORMACOES TRIMESTRAIS",
)


@dataclass(frozen=True)
class DomainConfig:
    """Domain-specific configuration container.

    Attributes:
        words_to_remove (Tuple[str, ...]): A tuple of words to be removed,
            initialized with the default value from ``WORDS_TO_REMOVE``.
    """

    # Configuration attributes with defaults from WORDS_TO_REMOVE
    words_to_remove: Tuple[str, ...] = field(default_factory=lambda: WORDS_TO_REMOVE)
    statements_types: Tuple[str, ...] = field(default_factory=lambda: STATEMENTS_TYPES)


def load_domain_config() -> DomainConfig:
    """Load the global domain configuration settings.

    Returns:
        GlobalSettingsConfig: An instance of GlobalSettingsConfig initialized
        with default constants for wait and threshold.
    """
    # Run domain settings using default constants
    return DomainConfig(
        words_to_remove=WORDS_TO_REMOVE,
        statements_types=STATEMENTS_TYPES,
    )
