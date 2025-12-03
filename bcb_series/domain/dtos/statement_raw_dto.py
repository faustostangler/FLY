from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

from .statement_fetched_dto import StatementFetchedDTO


@dataclass(frozen=True, kw_only=True)
class StatementRawDTO:
    """Immutable DTO representing a raw scraped financial statement row.

    Attributes:
        id (Optional[int]): Database ID if persisted, otherwise None.
        nsd (str): NSD identifier (must be numeric).
        company_name (Optional[str]): Company name, if available.
        quarter (Optional[str]): Financial quarter reference.
        version (Optional[str]): Version identifier of the statement.
        grupo (str): Group classification of the statement.
        quadro (str): Board classification of the statement.
        account (str): Account code extracted from the statement.
        description (str): Human-readable description of the account.
        value (float): Numeric value associated with the statement row.
    """

    id: Optional[int] = None
    nsd: str
    company_name: Optional[str]
    quarter: datetime
    version: Optional[str]
    grupo: str
    quadro: str
    account: str
    description: str
    value: float

    @staticmethod
    def from_dict(raw: dict[str, Any], *, cleandate: Callable[[object], datetime]) -> "StatementRawDTO":
        """Build a ``StatementRawDTO`` from a raw dictionary.

        Args:
            raw (dict): Input dictionary containing scraped statement data.

        Returns:
            StatementRawDTO: A validated and structured DTO.

        Raises:
            ValueError: If the ``nsd`` field is missing or not numeric.
        """
        # Validate and normalize NSD field
        nsd_raw = raw.get("nsd", "")
        if nsd_raw is None or not str(nsd_raw).isdigit():
            raise ValueError("Invalid NSD value")
        nsd_value = str(nsd_raw)
        q = cleandate(raw.get("quarter"))
        if q is None:
            raise ValueError("quarter obrigatório não informado ou inválido")

        # Construct and return a fully initialized DTO
        return StatementRawDTO(
            id=raw.get("id"),
            nsd=nsd_value,
            company_name=raw.get("company_name"),
            quarter=q,
            version=raw.get("version"),
            grupo=str(raw.get("grupo", "")),
            quadro=str(raw.get("quadro", "")),
            account=str(raw.get("account", "")),
            description=str(raw.get("description", "")),
            value=float(raw.get("value", 0.0)),
        )

    def to_fetched(self, target_line: str) -> "StatementFetchedDTO":
        """Convert this raw DTO into a ``StatementFetchedDTO``.

        Args:
            target_line (str): A formatted line containing account and description,
                separated by " - ". Example: "1234 - Cash and Equivalents".

        Returns:
            StatementFetchedDTO: The fetched statement with structured fields.
        """
        from .statement_fetched_dto import StatementFetchedDTO

        # Extract account and description from the target line
        parts = target_line.split(" - ", 1)
        account = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else self.description

        # Build and return the fetched DTO
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
        )
