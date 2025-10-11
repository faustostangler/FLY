from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

    @classmethod
    def from_string(cls, value: object | None) -> "Frequency":
        if isinstance(value, Frequency):
            return value
        normalized = str(value or "daily").strip().lower()
        for item in cls:
            if item.value == normalized:
                return item
        return cls.DAILY


class Coverage(Enum):
    FLOW = "flow"
    STOCK = "stock"
    AVERAGE = "average"

    @classmethod
    def from_string(cls, value: object | None) -> "Coverage":
        if isinstance(value, Coverage):
            return value
        normalized = str(value or "stock").strip().lower()
        for item in cls:
            if item.value == normalized:
                return item
        return cls.STOCK

    @property
    def is_flow(self) -> bool:
        return self is Coverage.FLOW


@dataclass(frozen=True)
class Period:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("Period end must be greater than or equal to start")

    @classmethod
    def from_frequency(cls, observation_date: datetime, frequency: Frequency) -> "Period":
        if frequency is Frequency.DAILY:
            start = end = observation_date
        elif frequency is Frequency.WEEKLY:
            weekday = observation_date.weekday()
            start = observation_date - timedelta(days=weekday)
            end = start + timedelta(days=6)
        elif frequency is Frequency.MONTHLY:
            start = observation_date.replace(day=1)
            next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
            end = next_month - timedelta(days=1)
        elif frequency is Frequency.QUARTERLY:
            quarter = (observation_date.month - 1) // 3
            start_month = quarter * 3 + 1
            start = observation_date.replace(month=start_month, day=1)
            next_quarter_month = start_month + 3
            if next_quarter_month > 12:
                next_quarter_month -= 12
                year = start.year + 1
            else:
                year = start.year
            next_quarter = start.replace(year=year, month=next_quarter_month, day=1)
            end = next_quarter - timedelta(days=1)
        elif frequency is Frequency.ANNUAL:
            start = observation_date.replace(month=1, day=1)
            end = observation_date.replace(month=12, day=31)
        else:
            start = end = observation_date

        if end < observation_date:
            end = observation_date

        return cls(start, end)

    def iter_days(self) -> list[datetime]:
        delta = self.end - self.start
        return [self.start + timedelta(days=offset) for offset in range(delta.days + 1)]

    @property
    def days_count(self) -> int:
        return (self.end - self.start).days + 1
