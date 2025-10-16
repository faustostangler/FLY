from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional


@dataclass(frozen=True, kw_only=True)
class StatementRatioDTO:
    """Immutable representation of a fetched and validated financial statement row.

    Attributes:
        id (Optional[int]): Unique identifier, if present in the database.
        nsd (str): Normalized security identifier (must be numeric).
        company_name (Optional[str]): Name of the company associated with the statement.
        quarter (Optional[str]): Reporting quarter (e.g., "Q1", "Q2").
        version (Optional[str]): Statement version if multiple revisions exist.
        grupo (str): Group classification of the account.
        quadro (str): Subsection or panel classification.
        account (str): Account identifier.
        description (str): Human-readable description of the account.
        value (float): Numeric value of the account entry.
    """

    id: Optional[int] = None
    nsd: str
    company_name: str
    date: datetime
    version: str
    grupo: str
    quadro: str
    account: str
    description: str
    value: float

    @staticmethod
    def from_dict(raw: dict[str, Any], *, cleandate: Callable[[object], datetime]) -> "StatementRatioDTO":
        """Convert a raw dictionary into a ``StatementRatioDTO``.

        Validates and coerces types where necessary to ensure the DTO
        is properly structured for downstream processing.

        Args:
            raw (dict): Input dictionary containing statement fields.

        Returns:
            StatementRatioDTO: A fully validated and normalized DTO.

        Raises:
            ValueError: If the NSD field is missing or not numeric.
        """
        # Extract and validate NSD, must be numeric
        nsd_raw = raw.get("nsd", "")
        if nsd_raw is None or not str(nsd_raw).isdigit():
            raise ValueError("Invalid NSD value")
        nsd_value = str(nsd_raw)
        d = cleandate(raw.get("date"))
        if d is None:
            raise ValueError("quarter obrigatório não informado ou inválido")

        # Build and return DTO with normalized fields
        return StatementRatioDTO(
            id=raw.get("id"),
            nsd=nsd_value,
            company_name=raw.get("company_name", ""),
            date=d,
            version=raw.get("version", ""),
            grupo=str(raw.get("grupo", "")),
            quadro=str(raw.get("quadro", "")),
            account=str(raw.get("account", "")),
            description=str(raw.get("description", "")),
            value=float(raw.get("value", 0.0)),
        )
