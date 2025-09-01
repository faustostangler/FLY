from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# Default set of phrases that should be stripped from company names
WORDS_TO_REMOVE: Tuple[str, ...] = (
    "EM LIQUIDACAO",
    "EM LIQUIDACAO EXTRAJUDICIAL",
    "EXTRAJUDICIAL",
    "EM RECUPERACAO JUDICIAL",
    "EM REC JUDICIAL",
    "EMPRESA FALIDA",
    "MASSA FALIDA DA",
)

# NsdTypePolicy financial statement types
STATEMENTS_TYPES: Tuple[str, ...] = (
    "DEMONSTRACOES FINANCEIRAS PADRONIZADAS",
    "INFORMACOES TRIMESTRAIS",
)

# Base currency used throughout the application
BASE_CURRENCY = "BRL"


@dataclass(frozen=True)
class DomainConfig:
    """Immutable configuration for domain-level business rules.

    Attributes:
        words_to_remove (Tuple[str, ...]): Phrases to remove from company names.
        statements_types (Tuple[str, ...]): Accepted types of financial statements.
        base_currency (str): Standard reporting currency (default: BRL).
        nsd_gap_days (int): Allowed gap in days for NSD processing. Defaults to 0.
    """

    # Phrases that must be stripped from company names
    words_to_remove: Tuple[str, ...] = WORDS_TO_REMOVE

    # Financial statement types considered valid
    statements_types: Tuple[str, ...] = STATEMENTS_TYPES

    # Default reporting currency
    base_currency: str = BASE_CURRENCY

    # Gap in days allowed for NSD events
    nsd_gap_days: int = 0


def load_domain_config() -> DomainConfig:
    """Factory function to load domain configuration.

    Returns:
        DomainConfig: Initialized with default constants for name cleaning,
        statement types, base currency, and NSD gap days.
    """
    # Construct and return the domain configuration with defaults
    return DomainConfig(
        words_to_remove=WORDS_TO_REMOVE,
        statements_types=STATEMENTS_TYPES,
        base_currency=BASE_CURRENCY,
        nsd_gap_days=0,
    )
