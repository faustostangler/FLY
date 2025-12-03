from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional


@dataclass(frozen=True, kw_only=True)
class NsdDTO:
    """Immutable Data Transfer Object (DTO) for NSD entries.

    Represents structured NSD (National Securities Depository) data
    extracted from the stock exchange.

    Attributes:
        id (Optional[int]): Internal identifier (may be None for new records).
        nsd (int): NSD numeric code, validated as a digit-only string before casting.
        company_name (str): Official company name associated with the NSD.
        quarter (Optional[datetime]): Reporting quarter timestamp, if available.
        version (Optional[str]): Version identifier of the filing.
        nsd_type (Optional[str]): Type/category of NSD report.
        dri (Optional[str]): Designated Responsible Individual.
        auditor (Optional[str]): Name of the auditing company.
        responsible_auditor (Optional[str]): Lead responsible auditor.
        protocol (Optional[str]): Protocol reference number.
        sent_date (Optional[datetime]): Date the NSD report was submitted.
        reason (Optional[str]): Justification or notes related to the filing.
    """

    id: Optional[int] = None
    nsd: int
    company_name: str
    quarter: datetime
    version: int
    nsd_type: Optional[str]
    dri: Optional[str]
    auditor: Optional[str]
    responsible_auditor: Optional[str]
    protocol: Optional[str]
    sent_date: datetime
    reason: Optional[str]

    @staticmethod
    def from_dict(raw: dict[str, Any], *, cleandate: Callable[[object], datetime]) -> Optional[NsdDTO]:
        """Build an ``NsdDTO`` from a raw scraped dictionary.

        Args:
            raw (dict): Dictionary containing scraped NSD fields.

        Returns:
            Optional[NsdDTO]: A fully initialized ``NsdDTO`` if valid,
            otherwise ``None`` when input is empty.

        Raises:
            ValueError: If the "nsd" field is missing or not a valid integer.
        """
        # Ensure input is not empty
        if not raw:
            return None

        # Validate NSD field before conversion
        nsd_raw = raw.get("nsd")
        if nsd_raw is None or not str(nsd_raw).isdigit():
            raise ValueError("Invalid NSD value")

        # Build DTO from sanitized input
        return NsdDTO(
            id=raw.get("id"),
            nsd=int(nsd_raw),
            company_name=str(raw.get("company_name") or ""),
            quarter=cleandate(raw.get("quarter")),
            version=int(''.join(c for c in str(raw.get("version") or 1) if c.isdigit())), # Normalized version
            nsd_type=raw.get("nsd_type"),
            dri=raw.get("dri"),
            auditor=raw.get("auditor"),
            responsible_auditor=raw.get("responsible_auditor"),
            protocol=raw.get("protocol"),
            sent_date=cleandate(raw.get("sent_date")),
            reason=raw.get("reason"),
        )

    @staticmethod
    def from_raw(raw: NsdDTO) -> NsdDTO:
        """Build an ``NsdDTO`` from another DTO-like object.

        Args:
            raw (NsdDTO): A DTO-like object with matching attributes.

        Returns:
            NsdDTO: A new immutable ``NsdDTO`` instance populated
            with the same values as the input.
        """
        return NsdDTO(
            id=getattr(raw, "id", None),
            nsd=raw.nsd,
            company_name=raw.company_name,
            quarter=raw.quarter,
            version=raw.version,
            nsd_type=raw.nsd_type,
            dri=raw.dri,
            auditor=raw.auditor,
            responsible_auditor=raw.responsible_auditor,
            protocol=raw.protocol,
            sent_date=raw.sent_date,
            reason=raw.reason,
        )
