"""DTO for transformed statement rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class StatementFetchedDTO:
    """Immutable representation of a cleaned statement row."""

    id: Optional[int] = None
    nsd: str
    company_name: Optional[str]
    quarter: Optional[str]
    version: Optional[str]
    grupo: str
    quadro: str
    account: str
    description: str
    value: float
    processing_hash: str = ""

    @staticmethod
    def from_dict(raw: dict) -> "StatementFetchedDTO":
        """Create ``StatementFetchedDTO`` from a raw dictionary."""
        nsd_raw = raw.get("nsd", "")
        if nsd_raw is None or not str(nsd_raw).isdigit():
            raise ValueError("Invalid NSD value")
        nsd_value = str(nsd_raw)

        return StatementFetchedDTO(
            id=raw.get("id"),
            nsd=nsd_value,
            company_name=raw.get("company_name"),
            quarter=raw.get("quarter"),
            version=raw.get("version"),
            grupo=str(raw.get("grupo", "")),
            quadro=str(raw.get("quadro", "")),
            account=str(raw.get("account", "")),
            description=str(raw.get("description", "")),
            value=float(raw.get("value", 0.0)),
            processing_hash=str(raw.get("processing_hash", "")),
        )
