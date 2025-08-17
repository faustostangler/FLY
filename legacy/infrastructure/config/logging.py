from dataclasses import dataclass, field
from pathlib import Path

from .paths import load_paths

LOG_FILENAME = "fly_logger.log"  # Nome do arquivo de log padrão
LEVEL = "INFO"  # Nível de log padrão
SHOW_IMPORT_PATH = False  # Include caller import path in logs


@dataclass(frozen=True)
class LoggingConfig:
    """Logging system configuration.

    Attributes:
        log_dir: Directory where logs will be saved.
        log_file_name: Name of the log file.
        level: Default logging level.
        full_path: Full path to the log file.
    """

    log_dir: Path
    log_file_name: str = field(default=LOG_FILENAME)
    level: str = field(default=LEVEL)
    show_path: bool = field(default=SHOW_IMPORT_PATH)

    @property
    def full_path(self) -> Path:
        return self.log_dir / self.log_file_name


def load_logging_config() -> LoggingConfig:
    """Creates and returns an instance of LoggingConfig, ensuring that the log
    directory exists.

    Returns:
        LoggingConfig: The logging configuration object with directory, filename, and level.
    """
    # Run application paths using the load_paths function
    paths = load_paths()

    # Return a LoggingConfig instance with the loaded log directory, default filename, and level
    return LoggingConfig(
        log_dir=paths.log_dir,
        log_file_name=LOG_FILENAME,
        level=LEVEL,
        show_path=SHOW_IMPORT_PATH,
    )
