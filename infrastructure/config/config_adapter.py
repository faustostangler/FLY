from dataclasses import dataclass, field

from .fly_settings import FlyConfig, load_fly_config


@dataclass(frozen=True)
class ConfigAdapter:
    fly_settings: FlyConfig = field(default_factory=load_fly_config)
