"""Command DTO for triggering the eligible companies projection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Mapping, Any


@dataclass(frozen=True)
class EligibleCompaniesCommandDTO:
    """Immutable input describing how to (re)calculate the projection.

    Attributes:
        version: Logical version identifier for the projection.
        window_start: Optional lower bound for considering statements/quotes.
        window_end: Optional upper bound for considering statements/quotes.
        rule_params: Extra parameters that fine tune the domain rules. Stored as
            an immutable mapping to avoid accidental mutations across layers.
    """

    version: str
    window_start: datetime | None = None
    window_end: datetime | None = None
    rule_params: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:  # pragma: no cover - dataclass hook
        object.__setattr__(
            self,
            "rule_params",
            MappingProxyType(dict(self.rule_params)),
        )
