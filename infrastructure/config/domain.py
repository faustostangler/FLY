from dataclasses import dataclass, field

WORDS_TO_REMOVE = [
    "EM LIQUIDACAO",
    "EM LIQUIDACAO EXTRAJUDICIAL",
    "EXTRAJUDICIAL",
    "EM RECUPERACAO JUDICIAL",
    "EM REC JUDICIAL",
    "EMPRESA FALIDA",
    "MASSA FALIDA DA", 
]

STATEMENTS_TYPES = [
    "DEMONSTRACOES FINANCEIRAS PADRONIZADAS",
    "INFORMACOES TRIMESTRAIS",
]


@dataclass(frozen=True)
class DomainConfig:
    """GlobalSettingsConfig holds global configuration settings for the
    application.

    Attributes:
        words_to_remove (list): A list of words to be removed, initialized with the default value from WORDS_TO_REMOVE.
    """

    # Configuration attributes with defaults from WORDS_TO_REMOVE
    words_to_remove: list = field(default_factory=lambda: WORDS_TO_REMOVE.copy())
    statements_types: list = field(default_factory=lambda: STATEMENTS_TYPES.copy())


def load_domain_config() -> DomainConfig:
    """Loads the global domain configuration settings.

    Returns:
        GlobalSettingsConfig: An instance of GlobalSettingsConfig initialized with default constants for wait and threshold.
    """

    # Run domain settings using default constants
    return DomainConfig(
        words_to_remove=WORDS_TO_REMOVE,
        statements_types=STATEMENTS_TYPES,
    )
