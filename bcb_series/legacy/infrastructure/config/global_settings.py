from dataclasses import dataclass, field

from infrastructure.config.version import get_version

VERSION = get_version(fallback_release="0.0.1")
APP_NAME = "FLY" + "/" + VERSION  # Application name

WAIT = 2  # Default wait time in seconds
MAX_LINEAR_HOLES = 200  # Maximum number of linear holes allowed

MAX_WORKERS = 1 # 20 Default number of threads for sync operations
THRESHOLD = 10 # (MAX_WORKERS)  # max(int(50 / MAX_WORKERS), 1)  # Default threshold for saving data
QUEUE_SIZE = 2 * MAX_WORKERS  # Max queue size for producer/consumer pipeline

BATCH_SIZE = 100  # Number of items per repository batch
REQUEST_TIMEOUT_SEC = 5.0


@dataclass(frozen=True)
class GlobalSettingsConfig:
    """GlobalSettingsConfig class holds global configuration settings.

    Attributes:
        wait (int): The waiting time, initialized with the value of WAIT.
        threshold (int): The threshold for saving, initialized with the value of THRESHOLD.

    Logic Steps:
    1. Define class attributes for configuration parameters. # Define attributes for wait and threshold
    2. Use 'field' to set default values from external constants (WAIT, THRESHOLD). # Set defaults using WAIT and THRESHOLD
    3. These settings can be used throughout the application for consistent configuration. # Use these settings app-wide
    """

    # Configuration attributes with defaults
    app_name: str = field(default=APP_NAME)
    wait: int = field(default=WAIT)
    threshold: int = field(default=THRESHOLD)
    max_linear_holes: int = field(default=MAX_LINEAR_HOLES)
    max_workers: int = field(default=MAX_WORKERS)
    batch_size: int = field(default=BATCH_SIZE)
    queue_size: int = field(default=QUEUE_SIZE)
    request_timeout_sec: float = field(default=REQUEST_TIMEOUT_SEC)
    user_agent: str = field(default=APP_NAME)


def load_global_settings_config() -> GlobalSettingsConfig:
    """Loads and returns a GlobalSettingsConfig instance with default global
    settings.

    Returns:
        GlobalSettingsConfig: An instance initialized with the default WAIT and THRESHOLD values.

    Logic Steps:
    1. Use the WAIT and THRESHOLD constants as configuration values.
    2. Create and return a GlobalSettingsConfig instance with these values.
    """

    # Run global settings using default constants
    return GlobalSettingsConfig(
        app_name=APP_NAME,
        wait=WAIT,
        threshold=THRESHOLD,
        max_linear_holes=MAX_LINEAR_HOLES,
        max_workers=MAX_WORKERS,
        batch_size=BATCH_SIZE,
        queue_size=QUEUE_SIZE,
        request_timeout_sec=REQUEST_TIMEOUT_SEC,
        user_agent=APP_NAME,
    )
