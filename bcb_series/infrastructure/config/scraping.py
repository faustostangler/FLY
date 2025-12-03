from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# Default connectivity check URL
TEST_INTERNET = "http://clients3.google.com/generate_204"

# Default timeout for each request (seconds)
TIMEOUT = 5

# Maximum number of retry attempts per request
MAX_ATTEMPTS = 5

# Maximum number of linear holes allowed in the NSD scraping process
MAX_LINEAR_HOLES = 200

# JSON resource files containing request headers and metadata
USER_AGENTS_JSON = "user_agents.json"
REFERERS_JSON = "referers.json"
LANGUAGES_JSON = "languages.json"


@dataclass(frozen=True)
class ScrapingConfig:
    """Immutable configuration for web scraping settings.

    Attributes:
        user_agents (List[str]): List of user-agent strings for HTTP requests.
        referers (List[str]): List of referer strings for HTTP requests.
        languages (List[str]): List of Accept-Language headers.
        test_internet (str): URL used to check internet connectivity.
        timeout (int): Maximum wait time per request (in seconds).
        max_attempts (int): Maximum retry attempts if a request fails.
    """

    # User-agent strings loaded from JSON
    user_agents: List[str]

    # Referer headers loaded from JSON
    referers: List[str]

    # Accept-Language headers loaded from JSON
    languages: List[str]

    # Connectivity check URL
    test_internet: str = field(default=TEST_INTERNET)

    # Request timeout in seconds
    timeout: int = field(default=TIMEOUT)

    # Maximum retry attempts
    max_attempts: int = field(default=MAX_ATTEMPTS)

    # Maximum number of linear holes allowed in the NSD scraping process
    linear_holes: int = field(default=MAX_LINEAR_HOLES)


def load_scraping_config() -> ScrapingConfig:
    """Factory function to build a ScrapingConfig instance.

    Loads scraping configuration from JSON resource files. If a file is missing
    or corrupted, a safe default value is used instead.

    Returns:
        ScrapingConfig: Initialized configuration object containing scraping
        headers, connectivity settings, and retry policies.
    """

    # Base directory where JSON files are located
    base = Path(__file__).parent

    def load_json(path: Path, default)  -> List[str]:
        """Helper to load a JSON file with fallback to default on error."""
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return default
        except json.JSONDecodeError:
            return default

    # Load configuration lists from JSON files, fallback to defaults if necessary
    user_agents = load_json(
        base / USER_AGENTS_JSON,
        ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36 FLYBot/1.0"]
    )
    referers = load_json(base / REFERERS_JSON, ["https://google.com"])
    languages = load_json(base / LANGUAGES_JSON, ["en-US,en;q=1.0"])

    # Construct and return the scraping configuration object
    return ScrapingConfig(
        user_agents=user_agents,
        referers=referers,
        languages=languages,
        test_internet=TEST_INTERNET,
        timeout=TIMEOUT,
        max_attempts=MAX_ATTEMPTS,
        linear_holes=MAX_LINEAR_HOLES
    )
