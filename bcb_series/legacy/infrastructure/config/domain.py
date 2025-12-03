from dataclasses import dataclass
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
    """GlobalSettingsConfig holds global configuration settings for the
    application.

    Attributes:
        words_to_remove (list): A list of words to be removed, initialized with the default value from WORDS_TO_REMOVE.
    """

    # Configuration attributes with defaults
    words_to_remove: Tuple[str, ...] = WORDS_TO_REMOVE
    statements_types: Tuple[str, ...] = STATEMENTS_TYPES
    base_currency: str = "BRL"
    nsd_gap_days: int = 0


def load_domain_config() -> DomainConfig:
    """Loads the global domain configuration settings.

    Returns:
        GlobalSettingsConfig: An instance of GlobalSettingsConfig initialized with default constants for wait and threshold.
    """

    # Run domain settings using default constants
    return DomainConfig(
        words_to_remove=WORDS_TO_REMOVE,
        statements_types=STATEMENTS_TYPES,
        base_currency="BRL",
        nsd_gap_days=0,
    )
