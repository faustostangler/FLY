from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class StatementParsedDTO:
    """Immutable representation of a parsed and validated financial statement row.

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
        processing_hash (str): Optional hash used for deduplication and integrity checks.
    """

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
    def from_dict(raw: dict) -> "StatementParsedDTO":
        """Convert a raw dictionary into a ``StatementParsedDTO``.

        Validates and coerces types where necessary to ensure the DTO
        is properly structured for downstream processing.

        Args:
            raw (dict): Input dictionary containing statement fields.

        Returns:
            StatementParsedDTO: A fully validated and normalized DTO.

        Raises:
            ValueError: If the NSD field is missing or not numeric.
        """
        # Extract and validate NSD, must be numeric
        nsd_raw = raw.get("nsd", "")
        if nsd_raw is None or not str(nsd_raw).isdigit():
            raise ValueError("Invalid NSD value")
        nsd_value = str(nsd_raw)

        # Build and return DTO with normalized fields
        return StatementParsedDTO(
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
