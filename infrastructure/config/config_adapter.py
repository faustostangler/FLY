from dataclasses import dataclass, field

from .database import DatabaseConfig, load_database_config
from .fly_settings import FlyConfig, load_fly_config
from .logger import LoggerConfig, load_logger_config
from .paths import PathConfig, load_paths


@dataclass(frozen=True)
class ConfigAdapter:
    paths: PathConfig = field(default_factory=load_paths)
    fly_settings: FlyConfig = field(default_factory=load_fly_config)
    database: DatabaseConfig = field(default_factory=load_database_config)
    logging: LoggerConfig = field(default_factory=load_logger_config)
