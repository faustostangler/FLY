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
    """Domain-specific configuration settings."""

    words_to_remove: Tuple[str, ...] = field(default_factory=lambda: WORDS_TO_REMOVE)
    statements_types: Tuple[str, ...] = field(default_factory=lambda: STATEMENTS_TYPES)


def load_domain_config() -> DomainConfig:
    """Load the domain configuration settings."""

    return DomainConfig(
        words_to_remove=WORDS_TO_REMOVE,
        statements_types=STATEMENTS_TYPES,
    )
