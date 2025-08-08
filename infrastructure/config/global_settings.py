"""Configuration values shared across the application."""

from dataclasses import dataclass, field

APP_NAME = "FLY"  # Application name

WAIT = 2  # Default wait time in seconds
THRESHOLD = 500  # Default threshold for saving data
MAX_LINEAR_HOLES = 200  # Maximum number of linear holes allowed
MAX_WORKERS = 1  # Default number of threads for sync operations
BATCH_SIZE = 100  # Number of items per repository batch
QUEUE_SIZE = 1 * MAX_WORKERS  # Max queue size for producer/consumer pipeline


@dataclass(frozen=True)
class GlobalSettingsConfig:
    """Global configuration settings.

    Attributes:
        wait: Default wait time in seconds.
        threshold: Threshold for saving data.
    """

    # Configuration attributes with defaults
    app_name: str = field(default=APP_NAME)
    wait: int = field(default=WAIT)
    threshold: int = field(default=THRESHOLD)
    max_linear_holes: int = field(default=MAX_LINEAR_HOLES)
    max_workers: int | None = field(default=MAX_WORKERS)
    batch_size: int = field(default=BATCH_SIZE)
    queue_size: int = field(default=QUEUE_SIZE)


def load_global_settings_config() -> GlobalSettingsConfig:
    """Load and return the global settings configuration.

    Returns:
        GlobalSettingsConfig: Instance initialized with default values.
    """
    return GlobalSettingsConfig(
        app_name=APP_NAME,
        wait=WAIT,
        threshold=THRESHOLD,
        max_linear_holes=MAX_LINEAR_HOLES,
        max_workers=MAX_WORKERS,
        batch_size=BATCH_SIZE,
        queue_size=QUEUE_SIZE,
    )
