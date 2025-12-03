from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from infrastructure.config.paths import load_paths

# Default log filename
LOG_FILENAME = "fly_logger.log"

# Default log level
LEVEL = "INFO"

# Whether to include caller import path in logs
SHOW_IMPORT_PATH = False


@dataclass(frozen=True)
class LoggerConfig:
    """Immutable configuration for the logging system.

    Attributes:
        log_dir (Path): Directory where log files are stored.
        log_file_name (str): Name of the log file (default: fly_logger.log).
        level (str): Default logging level (e.g., INFO, DEBUG).
        show_path (bool): Whether to include caller import path in logs.
        full_path (Path): Computed property with the absolute path
            to the log file.
    """

    # Directory where log files will be saved
    log_dir: Path

    # Log filename (default: fly_logger.log)
    log_file_name: str = field(default=LOG_FILENAME)

    # Default logging level
    level: str = field(default=LEVEL)

    # Whether to show caller path in log messages
    show_path: bool = field(default=SHOW_IMPORT_PATH)

    @property
    def full_path(self) -> Path:
        """Full path to the log file, combining log_dir and log_file_name."""
        return self.log_dir / self.log_file_name


def load_logger_config() -> LoggerConfig:
    """Factory function to create a logger configuration.

    Ensures the log directory is correctly loaded from project paths.

    Returns:
        LoggerConfig: Immutable configuration with log directory,
        filename, level, and caller path visibility.
    """
    # Load global project paths
    paths = load_paths()

    # Build and return the logger configuration object
    return LoggerConfig(
        log_dir=paths.log_dir,
        log_file_name=LOG_FILENAME,
        level=LEVEL,
        show_path=SHOW_IMPORT_PATH,
    )
