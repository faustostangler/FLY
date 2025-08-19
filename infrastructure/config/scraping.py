from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

TEST_INTERNET = (
    "http://clients3.google.com/generate_204"  # URL usada para verificar conectividade
)
TIMEOUT = 5  # Tempo máximo de espera em cada requisição (em segundos)
MAX_ATTEMPTS = 5  # Número máximo de tentativas em caso de falha

USER_AGENTS_JSON = "user_agents.json"  # Arquivo JSON com User-Agents
REFERERS_JSON = "referers.json"  # Arquivo JSON com Referers
LANGUAGES_JSON = "languages.json"  # Arquivo JSON com Accept-Language


@dataclass(frozen=True)
class ScrapingConfig:
    """General settings for web scraping.

    Attributes:
        test_internet: URL used to check connectivity.
        timeout: Maximum wait time for each request.
        max_attempts: Maximum retry attempts if a request fails.
        user_agents: List of user-agent strings loaded from ``user_agents.json``.
        referers: List of referer strings loaded from ``referers.json``.
        languages: List of Accept-Language headers from ``languages.json``.
    """

    user_agents: List[str]
    referers: List[str]
    languages: List[str]
    test_internet: str = field(default=TEST_INTERNET)
    timeout: int = field(default=TIMEOUT)
    max_attempts: int = field(default=MAX_ATTEMPTS)


def load_scraping_config() -> ScrapingConfig:
    """Create a :class:`ScrapingConfig` from bundled JSON files."""

    base = Path(__file__).parent

    def load_json(path: Path, default):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return default
        except json.JSONDecodeError:
            # if file exists but is broken
            return default

    base = Path(__file__).parent

    USER_AGENTS_JSON = "user_agents.json"
    REFERERS_JSON = "referers.json"
    LANGUAGES_JSON = "languages.json"

    user_agents = load_json(base / USER_AGENTS_JSON, ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36 FLYBot/1.0"])
    referers    = load_json(base / REFERERS_JSON,    ["https://google.com"])
    languages   = load_json(base / LANGUAGES_JSON,   ["en-US,en;q=1.0"])

    return ScrapingConfig(
        user_agents=user_agents,
        referers=referers,
        languages=languages,
        test_internet=TEST_INTERNET,
        timeout=TIMEOUT,
        max_attempts=MAX_ATTEMPTS,
    )
