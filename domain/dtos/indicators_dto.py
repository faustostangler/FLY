from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterable, Optional

from domain.value_objects.indicators import Coverage, Frequency, Period


@dataclass(frozen=True, kw_only=True)
class IndicatorRecordDTO:
    """Normalized representation of a single indicator datapoint."""

    id: Optional[int] = None
    source: str
    name: str
    code: str
    frequency: Frequency
    coverage: Coverage
    observation_period: Period
    observation_date: datetime
    availability_date: datetime
    value: float

    @property
    def observation_start(self) -> datetime:
        return self.observation_period.start

    @property
    def observation_end(self) -> datetime:
        return self.observation_period.end

    def to_daily(
        self, day: datetime, *, value: float, availability_date: datetime | None = None
    ) -> "IndicatorRecordDTO":
        """Create a daily version of the current record for the provided day."""

        return IndicatorRecordDTO(
            source=self.source,
            name=self.name,
            code=self.code,
            frequency=Frequency.DAILY,
            coverage=self.coverage,
            observation_period=Period(day, day),
            observation_date=day,
            availability_date=availability_date or self.availability_date,
            value=value,
        )

    @staticmethod
    def from_dict(
        raw: dict[str, Any], *, cleandate: Callable[[object], datetime]
    ) -> Optional["IndicatorRecordDTO"]:
        """Build a DTO from a raw scraped dictionary."""

        if not raw:
            return None

        frequency = Frequency.from_string(raw.get("frequency"))
        observation_start = cleandate(raw.get("observation_start") or raw.get("date"))
        observation_end = cleandate(raw.get("observation_end") or raw.get("date"))
        availability = cleandate(raw.get("availability_date") or raw.get("date"))

        return IndicatorRecordDTO(
            source=str(raw.get("source") or ""),
            name=str(raw.get("name") or ""),
            code=str(raw.get("code") or ""),
            frequency=frequency,
            coverage=Coverage.from_string(raw.get("coverage")),
            observation_period=Period(observation_start, observation_end),
            observation_date=observation_end,
            availability_date=availability,
            value=float(raw.get("value") or 0.0),
        )

    @staticmethod
    def from_raw(raw: "IndicatorRecordDTO") -> "IndicatorRecordDTO":
        """Build a DTO from another DTO-like object."""

        observation_period = getattr(raw, "observation_period", None)
        if not isinstance(observation_period, Period):
            observation_date = getattr(raw, "observation_date", datetime.min)
            observation_period = Period(observation_date, observation_date)

        return IndicatorRecordDTO(
            id=getattr(raw, "id", None),
            source=getattr(raw, "source", ""),
            name=getattr(raw, "name", ""),
            code=getattr(raw, "code", ""),
            frequency=getattr(raw, "frequency", Frequency.DAILY),
            coverage=getattr(raw, "coverage", Coverage.STOCK),
            observation_period=observation_period,
            observation_date=getattr(raw, "observation_date", observation_period.end),
            availability_date=getattr(
                raw, "availability_date", getattr(raw, "observation_date", observation_period.end)
            ),
            value=getattr(raw, "value", 0.0),
        )

    @staticmethod
    def ensure_iterable(items: Optional[Iterable["IndicatorRecordDTO"]]) -> list["IndicatorRecordDTO"]:
        """Return a list for any optional iterable of indicator records."""

        return list(items or [])
