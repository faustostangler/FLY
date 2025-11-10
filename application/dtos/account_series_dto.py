from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List


@dataclass
class AccountSeriesPointDTO:
    date: date
    value: float


@dataclass
class AccountSeriesDTO:
    ticker: str
    account_code: str
    label: str
    points: List[AccountSeriesPointDTO]
