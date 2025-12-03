from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccountCode:
    """Value object que representa um código de conta contábil."""

    value: str

    def __post_init__(self) -> None:
        v = self.value.strip()
        if not v:
            raise ValueError("AccountCode vazio")

        parts = v.split(".")
        if any(not part.isdigit() for part in parts):
            raise ValueError(f"AccountCode inválido: {v}")

        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return self.value
