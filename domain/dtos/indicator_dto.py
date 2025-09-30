from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, MutableMapping


@dataclass(frozen=True, slots=True)
class IndicatorRecordDTO:
    """Normalized representation of a single indicator datapoint."""

    origin: str
    name: str
    code: str
    date: datetime
    value: float


@dataclass(frozen=True, slots=True)
class IndicatorRawDTO:
    """Raw datapoint as returned by a specific external provider."""

    source: str
    payload: Mapping[str, object] | MutableMapping[str, object]
