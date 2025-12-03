from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .statement_fetched_dto import StatementFetchedDTO


@dataclass(frozen=True, kw_only=True)
class StatementRawDTO:
    """Immutable DTO representing a scraped statement row."""

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

    @staticmethod
    def from_dict(raw: dict) -> "StatementRawDTO":
        """Create a ``StatementRawDTO`` from a raw dictionary."""

        nsd_raw = raw.get("nsd", "")
        if nsd_raw is None or not str(nsd_raw).isdigit():
            raise ValueError("Invalid NSD value")
        nsd_value = str(nsd_raw)

        return StatementRawDTO(
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
        )

    def to_fetched(self, target_line: str) -> "StatementFetchedDTO":
        """Convert this raw row into a ``StatementFetchedDTO``."""

        from .statement_fetched_dto import StatementFetchedDTO

        parts = target_line.split(" - ", 1)
        account = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else self.description

        return StatementFetchedDTO(
            id=None,
            nsd=self.nsd,
            company_name=self.company_name,
            quarter=self.quarter,
            version=self.version,
            grupo=self.grupo,
            quadro=self.quadro,
            account=account,
            description=description,
            value=self.value,
            processing_hash="",
        )
