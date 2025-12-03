from __future__ import annotations

from dataclasses import dataclass

# Default application name
APP_NAME = "FLY"


@dataclass(frozen=True)
class FlyConfig:
    """Immutable configuration for application identity and runtime flags.

    Attributes:
        app_name (str): Application name combined with version identifier.
        version (str): Current version of the application.
        show_path (bool): Whether to display paths in logs or output. Defaults to False.
    """

    # Application name + version identifier
    app_name: str

    # Application version string
    version: str

    # Whether to show paths in runtime outputs/logs
    show_path: bool = False


def load_fly_config() -> FlyConfig:
    """Factory function to load Fly application settings.

    Returns:
        FlyConfig: Configuration containing app name, version, and display flags.
    """
    # Local import to avoid circular dependency
    from infrastructure.utils import get_version

    # Resolve current version (with fallback if unavailable)
    version = get_version(fallback_release="0.0.1")

    # Construct and return the FlyConfig instance
    return FlyConfig(
        app_name=APP_NAME + "/" + version,
        version=version,
        show_path=True,
    )
