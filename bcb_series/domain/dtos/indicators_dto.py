from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional


@dataclass(frozen=True, kw_only=True)
class IndicatorsDTO:
    """
    """

    id: Optional[int] = None
    source: str
    name: str
    code: str
    date: datetime
    value: Optional[float]

    @staticmethod
    def from_dict(raw: dict[str, Any], *, cleandate: Callable[[object], datetime]) -> Optional[IndicatorsDTO]:
        """Build an ``DTO`` from a raw scraped dictionary.

        Args:
            raw (dict): Dictionary containing external fields.

        Returns:
            Optional[DTO]: A fully initialized ``DTO`` if valid,
            otherwise ``None`` when input is empty.

        Raises:
            ValueError: If the field is missing or not a valid integer.
        """
        # Ensure input is not empty
        if not raw:
            return None

        # # Validate NSD field before conversion
        # nsd_raw = raw.get("nsd")
        # if nsd_raw is None or not str(nsd_raw).isdigit():
        #     raise ValueError("Invalid NSD value")

        # Build DTO from sanitized input
        return IndicatorsDTO(
            source=str(raw.get("name") or ""),
            name=str(raw.get("name") or ""),
            code=str(raw.get("name") or ""),
            date=cleandate(raw.get("date") or ""),
            value=float(raw.get("oen") or 0.0),
        )

    @staticmethod
    def from_raw(raw: IndicatorsDTO) -> IndicatorsDTO:
        """Build an ``DTO`` from another DTO-like object.

        Args:
            raw (DTO): A DTO-like object with matching attributes.

        Returns:
            DTO: A new immutable ``DTO`` instance populated
            with the same values as the input.
        """
        return IndicatorsDTO(
            id=getattr(raw, "id", None),
            source=getattr(raw, "source", ""),
            name=getattr(raw, "name", ""),
            code=getattr(raw, "code", ""),
            date=getattr(raw, "date", datetime.min),
            value=getattr(raw, "value", 0.0),
        )
