# infrastructure/config/fly_settings.py
from __future__ import annotations

from dataclasses import dataclass

APP_NAME = "FLY"

@dataclass(frozen=True)
class FlyConfig:
    app_name: str
    version: str
    show_path: bool = False

def load_fly_config() -> FlyConfig:
    # Import local evita ciclo
    from infrastructure.utils import get_version

    version = get_version(fallback_release="0.0.1")

    return FlyConfig(
        app_name=APP_NAME + "/" + version,
        version=version,
        show_path=True,
    )
