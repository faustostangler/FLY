from typing import Protocol, runtime_checkable


@runtime_checkable
class FlyConfig(Protocol):
    @property
    def app_name(self) -> str: ...

@runtime_checkable
class ConfigPort(Protocol):
    @property
    def fly_settings(self) -> FlyConfig: ...

