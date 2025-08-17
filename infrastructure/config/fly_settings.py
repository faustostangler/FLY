from dataclasses import dataclass, field

from infrastructure.utils import get_version

VERSION = get_version(fallback_release="0.0.1")
APP_NAME = "FLY" + "/" + VERSION  # Application name

@dataclass(frozen=True)
class FlyConfig:
    app_name: str = field(default=APP_NAME)

def load_fly_config() -> FlyConfig:

    # Run global settings using default constants
    return FlyConfig(
        app_name=APP_NAME,
    )