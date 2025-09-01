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

# items to scrape in exchange page
STATEMENT_ITEMS: Tuple[Dict[str, Optional[int | str]], ...] = (
    {
        "grupo": "DFs Individuais",
        "quadro": "Balanço Patrimonial Ativo",
        "informacao": 1,
        "demonstracao": 2,
        "periodo": 0,
    },
    {
        "grupo": "DFs Individuais",
        "quadro": "Balanço Patrimonial Passivo",
        "informacao": 1,
        "demonstracao": 3,
        "periodo": 0,
    },
    {
        "grupo": "DFs Individuais",
        "quadro": "Demonstração do Resultado",
        "informacao": 1,
        "demonstracao": 4,
        "periodo": 0,
    },
    {
        "grupo": "DFs Individuais",
        "quadro": "Demonstração do Resultado Abrangente",
        "informacao": 1,
        "demonstracao": 5,
        "periodo": 0,
    },
    {
        "grupo": "DFs Individuais",
        "quadro": "Demonstração do Fluxo de Caixa",
        "informacao": 1,
        "demonstracao": 99,
        "periodo": 0,
    },
    {
        "grupo": "DFs Individuais",
        "quadro": "Demonstração de Valor Adicionado",
        "informacao": 1,
        "demonstracao": 9,
        "periodo": 0,
    },
    {
        "grupo": "DFs Consolidadas",
        "quadro": "Balanço Patrimonial Ativo",
        "informacao": 2,
        "demonstracao": 2,
        "periodo": 0,
    },
    {
        "grupo": "DFs Consolidadas",
        "quadro": "Balanço Patrimonial Passivo",
        "informacao": 2,
        "demonstracao": 3,
        "periodo": 0,
    },
    {
        "grupo": "DFs Consolidadas",
        "quadro": "Demonstração do Resultado",
        "informacao": 2,
        "demonstracao": 4,
        "periodo": 0,
    },
    {
        "grupo": "DFs Consolidadas",
        "quadro": "Demonstração do Resultado Abrangente",
        "informacao": 2,
        "demonstracao": 5,
        "periodo": 0,
    },
    {
        "grupo": "DFs Consolidadas",
        "quadro": "Demonstração do Fluxo de Caixa",
        "informacao": 2,
        "demonstracao": 99,
        "periodo": 0,
    },
    {
        "grupo": "DFs Consolidadas",
        "quadro": "Demonstração de Valor Adicionado",
        "informacao": 2,
        "demonstracao": 9,
        "periodo": 0,
    },
    {
        "grupo": "Dados da Empresa",
        "quadro": "Composição do Capital",
        "informacao": None,
        "demonstracao": None,
        "periodo": 0,
    },
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

    # statements to scrape
    statement_items: Tuple[Dict[str, Optional[int | str]], ...] = STATEMENT_ITEMS

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
        statement_items=STATEMENT_ITEMS,
        base_currency=BASE_CURRENCY,
        nsd_gap_days=0,
    )
