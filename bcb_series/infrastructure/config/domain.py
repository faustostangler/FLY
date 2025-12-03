# infrastructure/config/domain.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

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

DEFAULT_NSD_GAP_DAYS = 0
DEFAULT_RECENCY_YEAR = datetime.now().year - 1

@dataclass(frozen=True)
class DomainConfig:
    """Immutable configuration for domain-level business rules.

    Attributes:
        words_to_remove: Phrases to remove from company names.
        statements_types: Accepted types of financial statements.
        base_currency: Standard reporting currency (default: BRL).
        nsd_gap_days: Allowed gap in days for NSD processing.
        recency_year: Ano mínimo aceito para considerar "recente" no NSD/Statements.
                      Use 0 para desabilitar o filtro.
    """

    words_to_remove: Tuple[str, ...] = WORDS_TO_REMOVE
    statements_types: Tuple[str, ...] = STATEMENTS_TYPES
    base_currency: str = BASE_CURRENCY
    nsd_gap_days: int = DEFAULT_NSD_GAP_DAYS
    recency_year: int = DEFAULT_RECENCY_YEAR

def load_domain_config() -> DomainConfig:
    """Factory function to load domain configuration."""
    return DomainConfig(
        words_to_remove=WORDS_TO_REMOVE,
        statements_types=STATEMENTS_TYPES,
        base_currency=BASE_CURRENCY,
        nsd_gap_days=DEFAULT_NSD_GAP_DAYS,
        recency_year=DEFAULT_RECENCY_YEAR,
    )
