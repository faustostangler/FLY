from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Union

DateLike = Union[date, datetime]


@dataclass(frozen=True)
class AccountSeriesPointDTO:
    date: DateLike
    value: Optional[float]


@dataclass(frozen=True)
class AccountSeriesDTO:
    ticker: Optional[str]
    account_code: str
    label: str
    points: List[AccountSeriesPointDTO]
