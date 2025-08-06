"""Infrastructure port: loads all configuration objects and aggregates them.
This is the composition root for configuration."""

from .config import Config
from .database import load_database_config
from .domain import load_domain_config
from .exchange_api import load_exchange_api_config
from .global_settings import load_global_settings_config
from .logging import load_logging_config
from .paths import load_paths
from .scraping import load_scraping_config
from .statements import load_statements_config
from .transformers import load_transformers_config


def load_config() -> Config:
    """Aggregate all configs into a Config instance."""
    return Config(
        paths=load_paths(),
        database=load_database_config(),
        exchange=load_exchange_api_config(),
        scraping=load_scraping_config(),
        logging=load_logging_config(),
        global_settings=load_global_settings_config(),
        domain=load_domain_config(),
        statements=load_statements_config(),
        transformers=load_transformers_config(),
    )
